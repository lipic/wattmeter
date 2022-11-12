import json
import uasyncio as asyncio
import time
import math

class Evse():
 
    
    def __init__(self, wattmeter,evse, __config__):
        self.evseInterface = evse
        self.dataLayer = DataLayer()
        self.setting = __config__
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
        status = []
        self.dataLayer.data['NUMBER_OF_EVSE'] = int(self.setting.config["in,EVSE-NUMBER"])
        for i in range(0,self.dataLayer.data['NUMBER_OF_EVSE']):
            try:
                status.append(await self.__readEvse_data(1000,3,ID=(i+1)))
            except Exception as e:
                print("evseHandler with ID: {} error: {}".format((i+1),e))
                #raise Exception("evseHandler with ID: {} error: {}".format((i+1),e))
        current = self.balancingEvseCurrent()
        currentContribution = self.currentEvse_Contribution(current)
        for i in range(0,self.dataLayer.data['NUMBER_OF_EVSE']):
            try:
                if((status[i] == 'SUCCESS_READ') == True):
                    if(self.setting.config["sw,ENABLE CHARGING"] == '1'):
                        if(self.setting.config["sw,WHEN AC IN: CHARGING"] == '1'):
                            if self.wattmeter.dataLayer.data["A"] == 1:
                                if (self.setting.config["sw,ENABLE BALANCING"] == '1'):
                                    current = next(currentContribution)
                                    #print("EVSE:{} with current: {}".format(i+1,current))
                                    async with self.evseInterface as e:
                                        await e.writeEvseRegister(1000,[current],i+1)
                                else:
                                    current = int(self.setting.config["inp,EVSE{}".format(i+1)])
                                    async with self.evseInterface as e:
                                        await e.writeEvseRegister(1000,[current],i+1)
                            else:
                                async with self.evseInterface as e:
                                    await e.writeEvseRegister(1000,[0],i+1)
                        else:
                            if (self.setting.config["sw,ENABLE BALANCING"] == '1'):
                                #if self.dataLayer.data['NUMBER_OF_EVSE'] > 1:
                                current = next(currentContribution)
                                #print("EVSE:{} with current: {}".format(i+1,current))
                                async with self.evseInterface as e:
                                    await e.writeEvseRegister(1000,[current],i+1)
                            else:
                                current = int(self.setting.config["inp,EVSE{}".format(i+1)])
                                async with self.evseInterface as e:
                                    await e.writeEvseRegister(1000,[current],i+1)
                    else: 
                        async with self.evseInterface as e:
                            await e.writeEvseRegister(1000,[0],i+1)
            except Exception as e:
                raise Exception("evseHandler error: {}".format(e))
        return "Read: {}; Write: {}".format(status,state)
          
        
    async def __readEvse_data(self,reg,length,ID):
        try:
            async with self.evseInterface as e:
                receiveData =  await e.readEvseRegister(reg,length,ID)
                
            if reg == 1000 and (receiveData != "Null") and (receiveData):
                if len(self.dataLayer.data["ACTUAL_CONFIG_CURRENT"])<ID:
                    self.dataLayer.data["ACTUAL_CONFIG_CURRENT"].append(int(((receiveData[0]) << 8)  | receiveData[1]))
                    self.dataLayer.data["ACTUAL_OUTPUT_CURRENT"].append(int(((receiveData[2]) << 8)  | receiveData[3]))
                    self.dataLayer.data["EV_STATE"].append(int(((receiveData[4]) << 8)  | receiveData[5]))
                    self.dataLayer.data["EV_COMM_ERR"].append(0)
                else:
                    self.dataLayer.data["ACTUAL_CONFIG_CURRENT"][ID-1] = int(((receiveData[0]) << 8)  | receiveData[1])
                    self.dataLayer.data["ACTUAL_OUTPUT_CURRENT"][ID-1] = int(((receiveData[2]) << 8)  | receiveData[3])
                    self.dataLayer.data["EV_STATE"][ID-1] = int(((receiveData[4]) << 8)  | receiveData[5])
                    self.dataLayer.data["EV_COMM_ERR"][ID-1] = 0
                return 'SUCCESS_READ'
                        
            else: 
                return "Timed out waiting for result."
                 
        except Exception as e:
            if reg == 1000:
                if len(self.dataLayer.data["EV_COMM_ERR"])<ID:
                    self.dataLayer.data["EV_COMM_ERR"].append(0)
                    self.dataLayer.data["ACTUAL_CONFIG_CURRENT"].append(0)
                    self.dataLayer.data["ACTUAL_OUTPUT_CURRENT"].append(0)
                    self.dataLayer.data["EV_STATE"].append(0)
                else:
                    self.dataLayer.data["EV_COMM_ERR"][ID-1] += 1
                    if(self.dataLayer.data["EV_COMM_ERR"][ID-1] > 30): 
                        self.dataLayer.data["ACTUAL_CONFIG_CURRENT"][ID-1] = 0
                        self.dataLayer.data["ACTUAL_OUTPUT_CURRENT"][ID-1] = 0
                        self.dataLayer.data["EV_STATE"][ID-1] = 0
                        self.dataLayer.data["EV_COMM_ERR"][ID-1] = 31
            
            raise Exception("__readEvse_data error: {}".format(e))

    def balancingEvseCurrent(self):
        I1 = 0
        I2 = 0
        I3 = 0
        maxCurrent = 0
        sumCurrent = 0
        avgCurrent = 0
        delta = 0
        
        
        if self.wattmeter.dataLayer.data["I1"] > 32767:
            I1 = self.wattmeter.dataLayer.data["I1"] - 65535
        else:
            I1 = self.wattmeter.dataLayer.data["I1"]

        if self.wattmeter.dataLayer.data["I2"] > 32767:
            I2 = self.wattmeter.dataLayer.data["I2"] - 65535
        else:
            I2 = self.wattmeter.dataLayer.data["I2"]
            
        if self.wattmeter.dataLayer.data["I3"] > 32767:
            I3 = self.wattmeter.dataLayer.data["I3"] - 65535
        else:
            I3 = self.wattmeter.dataLayer.data["I3"]

        if (I1 > I2)and(I1 > I3):
            maxCurrent = int(round(I1/100.0))

        if (I2 > I1)and(I2 > I3):
            maxCurrent = int(round(I2/100.0))
            
        if (I3 > I1)and(I3 > I2):
            maxCurrent = int(round(I3/100.0))
            
        sumCurrent = I1 + I2 + I3
        avgCurrent = int(round(sumCurrent / 300))

        HDO = False
        if (1 == self.wattmeter.dataLayer.data["A"]) and (1 == int(self.setting.config['sw,WHEN AC IN: CHARGING'])):
            HDO = True

        if self.setting.config["btn,PHOTOVOLTAIC"] == '1' and HDO==False:
            delta = int(self.setting.config["in,PV-GRID-ASSIST-A"]) - int(round(I1/100.0))

        elif self.setting.config["btn,PHOTOVOLTAIC"] == '2'  and HDO==False:
            delta = int(self.setting.config["in,PV-GRID-ASSIST-A"]) - avgCurrent
            
        else:
            delta = int(self.setting.config["in,MAX-CURRENT-FROM-GRID-A"]) - maxCurrent
            
        if maxCurrent > int(self.setting.config["in,MAX-CURRENT-FROM-GRID-A"]):
            delta = int(self.setting.config["in,MAX-CURRENT-FROM-GRID-A"]) - maxCurrent

        self.__cntCurrent = self.__cntCurrent+1
        #Dle normy je zmena proudu EV nasledujici po zmene pracovni cyklu PWM maximalne 5s
        breaker = int(self.setting.config["in,MAX-CURRENT-FROM-GRID-A"])
        if (breaker*0.5 + delta)< 0:
            self.__requestCurrent = 0
            self.__regulationDelay = 1

        elif self.__cntCurrent >= 2:
            if delta < 0:
                self.__requestCurrent = self.__requestCurrent + delta
                self.regulationLock1 = True
                self.lock1Counter = 1

            elif self.__regulationDelay > 0:
                self.__requestCurrent  = 0
                        
            elif not self.regulationLock1:
                if (delta)>=6 and self.checkIfEVisConnected():
                    self.__requestCurrent = self.__requestCurrent + 1
                elif self.checkIfEVisCharging():
                    self.__requestCurrent = self.__requestCurrent + 1
                else:
                    pass

            self.__cntCurrent = 0
            
       # print("self.regulationLock1",self.regulationLock1)
        if self.lock1Counter>=30:
            self.lock1Counter = 0
            self.regulationLock1 = False
                
        if (self.regulationLock1 == True) or (self.lock1Counter > 0):
            self.lock1Counter = self.lock1Counter + 1
            
        if self.__regulationDelay>0:
            self.__regulationDelay = self.__regulationDelay +1
        if self.__regulationDelay>60:
            self.__regulationDelay = 0
        sum = 0
        for i in range(0,self.dataLayer.data['NUMBER_OF_EVSE']):
            sum += int(self.setting.config["inp,EVSE{}".format(i+1)])
        
        if self.__requestCurrent > sum:
            self.__requestCurrent = sum

        #print("Request current: {}A".format(self.__requestCurrent))
        if self.__requestCurrent < 0 :
            self.__requestCurrent = 0
        return  self.__requestCurrent

    def currentEvse_Contribution(self,current):
        activeEvse = 0
        connectedEvse = 0

        for i in range(0,self.dataLayer.data['NUMBER_OF_EVSE']):
            if self.dataLayer.data["EV_STATE"][i] == 3:
                activeEvse += 1
            if self.dataLayer.data["EV_STATE"][i] >= 2: #pripojen nebo nabiji
                connectedEvse+=1

        if activeEvse == 0:
            activeEvse = 1

        pom = 0
        if connectedEvse != 0:
            pom = current/connectedEvse

        length = connectedEvse
        contibutinCurrent = [i for i in range(0,self.dataLayer.data['NUMBER_OF_EVSE'])]
        #print("POM:{}A, LEN:{}".format(pom,length))        
        for i in range(self.dataLayer.data['NUMBER_OF_EVSE'],0,-1):
            if self.dataLayer.data["EV_STATE"][i-1] >= 2:
                if pom<6:
                    length -= 1
                    contibutinCurrent[i-1]=0
                    if length != 0:
                        pom = current/length
                else:
                    contibutinCurrent[i-1]=int(pom)

            else:
                contibutinCurrent[i-1] = 0 

        i = 0
        while i<self.dataLayer.data['NUMBER_OF_EVSE']:
            if contibutinCurrent[i] > int(self.setting.config["inp,EVSE{}".format(i+1)]):
                contibutinCurrent[i] = int(self.setting.config["inp,EVSE{}".format(i+1)])
            yield contibutinCurrent[i]
            i += 1

    def checkIfEVisConnected(self):
        for i in range(0,self.dataLayer.data['NUMBER_OF_EVSE']):
            if self.dataLayer.data["EV_STATE"][i] == 2: #pripojen nebo nabiji
                return True
        return False

    def checkIfEVisCharging(self):
        for i in range(0,self.dataLayer.data['NUMBER_OF_EVSE']):
            if self.dataLayer.data["EV_STATE"][i] == 3: #pripojen nebo nabiji
                return True
        return False
        
class DataLayer:
    def __str__(self):
        return json.dumps(self.data)
        
    def __init__(self):
        self.data = {}
        self.data["ACTUAL_CONFIG_CURRENT"] = []
        self.data["ACTUAL_OUTPUT_CURRENT"] = []
        self.data["EV_STATE"] = []
        self.data["EV_COMM_ERR"] = []
        self.data["NUMBER_OF_EVSE"] = 0