import uasyncio as asyncio
import time
from main import __config__

class Evse():
 
    
    def __init__(self, wattmeter,evse):
        self.evseInterface = evse
        self.dataLayer = DataLayer()
        self.setting = __config__.Config()
        self.wattmeter = wattmeter
        self.regulationLock1 = False
        self.lock1Counter = 0
        self.__regulationDelay = 0
        self.__cntCurrent = 0
        self.__requestCurrent = 0
    
    async def evseHandler(self):
        #first read data from evse
        current = 0
        state = ""
        status = ''
        setting = self.setting.getConfig()
        self.dataLayer.data['NUMBER_OF_EVSE'] = setting["in,EVSE-NUMBER"]
        for i in range(0,int(self.dataLayer.data['NUMBER_OF_EVSE'])):
            try:
                status = await self.__readEvse_data(1000,3,ID=(i+1))
                if((status == 'SUCCESS_READ') == True):
                    #If get max current accordig to wattmeter
                    if(setting["sw,ENABLE CHARGING"] == '1'):
                        if (setting["sw,ENABLE BALANCING"] == '1'):
                            current = self.balancEvseCurrent(i)
                            print(current)
                            state = await self.evseInterface.writeEvseRegister(1000,[current],i+1)
                        else:
                            current = int(setting["sl,EVSE"])
                            state = await self.evseInterface.writeEvseRegister(1000,[current],i+1)    
                    else: 
                        state = await self.evseInterface.writeEvseRegister(1000,[0],i+1)
            except Exception as e:
                raise Exception("evseHandler error: {}".format(e))
        return "Read: {}; Write: {}".format(status,state)
          
        
    async def __readEvse_data(self,reg,length,ID):
        try:
            receiveData = await self.evseInterface.readEvseRegister(reg,length,ID)
            if (reg == 1000 and (receiveData != "Null") and (receiveData)):
                if(len(self.dataLayer.data["ACTUAL_CONFIG_CURRENT"])<ID):
                    self.dataLayer.data["ACTUAL_CONFIG_CURRENT"].append((int)((((receiveData[0])) << 8)  | ((receiveData[1]))))
                    self.dataLayer.data["ACTUAL_OUTPUT_CURRENT"].append((int)((((receiveData[2])) << 8)  | ((receiveData[3]))))
                    self.dataLayer.data["EV_STATE"].append((int)((((receiveData[4])) << 8)  | ((receiveData[5]))))
                else:
                    self.dataLayer.data["ACTUAL_CONFIG_CURRENT"][ID-1] =     (int)((((receiveData[0])) << 8)  | ((receiveData[1])))
                    self.dataLayer.data["ACTUAL_OUTPUT_CURRENT"][ID-1] =     (int)((((receiveData[2])) << 8)  | ((receiveData[3])))
                    self.dataLayer.data["EV_STATE"][ID-1] =     (int)((((receiveData[4])) << 8)  | ((receiveData[5])))
                
                return 'SUCCESS_READ'
                        
            else: 
                return "Timed out waiting for result."
                 
        except Exception as e:
            raise Exception("__readEvse_data error: {}".format(e))

    def balancEvseCurrent(self,ID):
        I1_P = 0
        I2_P = 0
        I3_P = 0
        I1_N = 0
        I2_N = 0
        I3_N = 0
        maxCurrent = 0
        if (self.wattmeter.dataLayer.data["I1"] > 32767):
            I1_N = self.wattmeter.dataLayer.data["I1"] - 65535
        else:
            I1_P = self.wattmeter.dataLayer.data["I1"]

        if (self.wattmeter.dataLayer.data["I2"] > 32767):
            I2_N = self.wattmeter.dataLayer.data["I2"] - 65535
        else:
            I2_P = self.wattmeter.dataLayer.data["I2"]
            
        if (self.wattmeter.dataLayer.data["I3"] > 32767):
            I3_N = self.wattmeter.dataLayer.data["I3"] - 65535
        else:
            I3_P = self.wattmeter.dataLayer.data["I3"]

        if((I1_P > I2_P)and(I1_P > I3_P)):
            maxCurrent = int(I1_P/100)

        if((I2_P > I1_P)and(I2_P > I3_P)):
            maxCurrent = int(I2_P/100)
            
        if((I3_P > I1_P)and(I3_P > I2_P)):
            maxCurrent = int(I3_P/100)
            
        delta = int(self.setting.config["sl,BREAKER"]) - maxCurrent
        print("Max Current: {}, Delta: {} ".format(maxCurrent,delta))
        # Kdyz je proud vetsi nez dvojnasobek proudu jsitice okamzite vypni a pak pockej 10s
      #  if ((maxCurrent <= int(self.setting.config["sl,BREAKER"])  * 2) and (0 == self.__Delay_for_breaker)) :
        self.__cntCurrent = self.__cntCurrent+1
        #Dle normy je zmena proudu EV nasledujici po zmene pracovni cyklu PWM maximalne 5s
        if (self.__cntCurrent >= 3) :
            if (int(self.dataLayer.data["EV_STATE"][ID]) != 3):
                if(delta < 0):
                    self.__requestCurrent = 0
                else:
                    if(self.__regulationDelay>0):
                        self.__requestCurrent  = 0
                    else:
                        self.__requestCurrent  = 6
            else :
                # kdyz proud presahne proud jistice, tak odecti deltu od nastavovaneho proudu
                if (delta < 0):
                    if((self.__requestCurrent + delta)< 0):
                        self.__requestCurrent = 0
                    else:
                        if((self.__requestCurrent + delta)<6):
                            self.__regulationDelay = 1
                        self.__requestCurrent = self.__requestCurrent + delta
                        self.regulationLock1 = True
                        self.lock1Counter = 1
                        
                else:
                    if((self.regulationLock1 != True)):
                        self.__requestCurrent  = self.__requestCurrent + 1

            self.__cntCurrent = 0
            
       # print("self.regulationLock1",self.regulationLock1)
        if(self.lock1Counter>=30):
            self.lock1Counter = 0
            self.regulationLock1 = False
                
        if((self.regulationLock1 == True) or (self.lock1Counter > 0)):                        
            self.lock1Counter = self.lock1Counter + 1
            
        if(self.__regulationDelay>0):
            self.__regulationDelay = self.__regulationDelay +1
        if(self.__regulationDelay>60):
            self.__regulationDelay = 0
        
        if(self.__requestCurrent > int(self.setting.config["sl,EVSE"])):
            self.__requestCurrent = int(self.setting.config["sl,EVSE"])
        
        return  self.__requestCurrent

        
class DataLayer:
    def __init__(self):
        self.data = {}
        self.data["ACTUAL_CONFIG_CURRENT"] = []
        self.data["ACTUAL_OUTPUT_CURRENT"] = []
        self.data["EV_STATE"] = []
        self.data["NUMBER_OF_EVSE"] = 0