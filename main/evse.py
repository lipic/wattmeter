import modbus
from machine import UART
import uasyncio as asyncio
from machine import Pin
import time
from main import __config__
import math

class Evse():

    
    def __init__(self,baudrate, wattmeter,lock):
        self.lock = lock
        self.DE = Pin(15, Pin.OUT) 
        self.uart =  UART(2,baudrate, bits=8, parity=None)
        self.modbusClient = modbus.Modbus()
        self.dataLayer = DataLayer()
        self.setting = __config__.Config()

        self.wattmeter = wattmeter
        self.regulationLock1 = False
        self.regulationLock2 = False
        self.regulationLock3 = False
        self.lock1Counter = 0
        self.lock2Counter = 0
        self.lock3Counter = 0
        self.secondWarning = False
        self.__cntCurrent = 0
        self.__requestCurrent = 0
                
    
    async def evseHandler(self):
        #first read data from evse
        current = 0
        state = ""
        status = ''
        status = await self.__readEvse_data(1000,3)
        setting = self.setting.getConfig()
        if((status == 'SUCCESS_READ') == True):
            #If get max current accordig to wattmeter
            if(setting["sw,ENABLE CHARGING"] == '1'):
                if (setting["sw,ENABLE BALANCING"] == '1'):
                    current = self.balancEvseCurrent()
                   # print("Setting current: ",current)
                    state = await self.writeEvseRegister(1000,[current])
                else:
                    current = int(setting["sl,EVSE"])
                    state = await self.writeEvseRegister(1000,[current])
                    
            else: 
                state = await self.writeEvseRegister(1000,[0])
                
        return "Read: {}; Write: {}".format(status,state)
        
    async def writeEvseRegister(self,reg,data):
        await self.lock.acquire()
        writeRegs = self.modbusClient.write_regs(reg, data)
        self.uart.write(writeRegs)
        self.DE.on()
        await asyncio.sleep_ms(50)
        receiveData = self.uart.read()
        self.DE.off() 
        self.lock.release()
        receiveData = receiveData [1:]
        try:
            if (0 == self.modbusClient.mbrtu_data_processing(receiveData)):
                data = bytearray()
                data.append(receiveData[2])
                data.append(receiveData[3])
                return data
            else:
                return 'ERROR'
        except Exception as e:
            return "Exception: {}".format(e)
        
    async def readEvseRegister(self,reg,length):
      #  await self.lock.acquire()
        readRegs = self.modbusClient.read_regs(reg, length)
        self.uart.write(readRegs)
        self.DE.on() 
        await asyncio.sleep_ms(50)
        receiveData = self.uart.read()
        self.DE.off() 
    #    self.lock.release()
        receiveData = receiveData [1:]
        try:
            if (receiveData  and  (0 == self.modbusClient.mbrtu_data_processing(receiveData))):
                data = bytearray()
                for i in range(0,(length*2)):
                    data.append(receiveData[i+3])
                return data
            else:
                return "Null"
        except Exception as e:
            return "Error"
        
        
    async def __readEvse_data(self,reg,length):
        
        receiveData = await self.readEvseRegister(reg,length)
        try:             
            if (reg == 1000):
                self.dataLayer.data["ACTUAL_CONFIG_CURRENT"] =     (int)((((receiveData[0])) << 8)  | ((receiveData[1])))
                self.dataLayer.data["ACTUAL_OUTPUT_CURRENT"] =     (int)((((receiveData[2])) << 8)  | ((receiveData[3])))
                self.dataLayer.data["EV_STATE"] =     (int)((((receiveData[4])) << 8)  | ((receiveData[5])))
                return 'SUCCESS_READ'
                        
            else: 
                return "Timed out waiting for result."
                 
        except Exception as e:
            return "Exception: {} ".format(e)

    def balancEvseCurrent(self):
        I1_P = 0
        I2_P = 0
        I3_P = 0
        I1_N = 0
        I2_N = 0
        I3_N = 0

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
        self.dataLayer.data["EV_STATE"]  = 3
        # Kdyz je proud vetsi nez dvojnasobek proudu jsitice okamzite vypni a pak pockej 10s
      #  if ((maxCurrent <= int(self.setting.config["sl,BREAKER"])  * 2) and (0 == self.__Delay_for_breaker)) :
        self.__cntCurrent = self.__cntCurrent+1
        #Dle normy je zmena proudu EV nasledujici po zmene pracovni cyklu PWM maximalne 5s
        if (self.__cntCurrent >= 3) :
            if (self.dataLayer.data["EV_STATE"] != 3):
                if(delta < 0):
                    self.__requestCurrent = 0
                else:
                    self.__requestCurrent  = int(self.setting.config["sl,EVSE"])
            else :
                # kdyz proud presahne proud jistice, tak odecti deltu od nastavovaneho proudu
                if (delta < 0):
                    if((self.__requestCurrent + delta)< 0):
                        self.__requestCurrent = 0
                    else:
                        self.__requestCurrent = self.__requestCurrent + delta
                        self.regulationLock1 = True
                        self.lock1Counter = 1
                        
                else:
                    if((self.regulationLock1 != True)):
                        self.__requestCurrent  = self.__requestCurrent + delta

            self.__cntCurrent = 0
            
       # print("self.regulationLock1",self.regulationLock1)
        if(self.lock1Counter>=30):
            self.lock1Counter = 0
            self.regulationLock1 = False
                
        if((self.regulationLock1 == True) or (self.lock1Counter > 0)):                        
            self.lock1Counter = self.lock1Counter + 1
        
        if(self.__requestCurrent > int(self.setting.config["sl,EVSE"])):
            self.__requestCurrent = int(self.setting.config["sl,EVSE"])
        
        return  self.__requestCurrent
    
class DataLayer:
    def __init__(self):
        self.data = {}
        self.data["ACTUAL_CONFIG_CURRENT"] = 0
        self.data["ACTUAL_OUTPUT_CURRENT"] = 0
        self.data["EV_STATE"] = 0