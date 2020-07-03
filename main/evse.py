from main import modbus
from machine import UART
import uasyncio as asyncio
from machine import Pin
import time
from main import __config__

class Evse():

    
    def __init__(self,baudrate, wattmeter,lock):
        self.lock = lock
        self.DE = Pin(15, Pin.OUT) 
        self.uart =  UART(2,baudrate, bits=8, parity=None)
        self.modbusClient = modbus.Modbus()
        self.dataLayer = DataLayer()
        self.setting = __config__.Config()

        self.wattmeter = wattmeter
        self.__Delay_for_breaker = 0
        self.__cntCurrent = 0
        self.__requestCurrent = 0
                
    
    async def evseHandler(self):
        #first read data from evse
        current = 0
        state = ""
        status = ''
        #status = await self.__readEvse_data(1000,3)
        setting = self.setting.getConfig()
        if((status == 'SUCCESS_READ') == True):
            #If get max current accordig to wattmeter
            if(setting["sw,ENABLE CHARGING"] == '1'):
                if (setting["sw,ENABLE BALANCING"] == '1'):
                    current = self.balancEvseCurrent()
                    state = await self.writeEvseRegister(1000,[current])
                else:
                    current = setting["sl,BREAKER"]
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
        await self.lock.acquire()
        readRegs = self.modbusClient.read_regs(reg, length)
        self.uart.write(readRegs)
        self.DE.on() 
        await asyncio.sleep_ms(50)
        receiveData = self.uart.read()
        self.DE.off() 
        self.lock.release()
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
        I1 = 0
        I2 = 0
        I3 = 0
        import math

        if (self.wattmeter.dataLayer.data["I1"] > 32767):
            I1 = self.wattmeter.dataLayer.data["I1"] - 65535
        else:
            I1 = self.wattmeter.dataLayer.data["I1"]

        if (self.wattmeter.dataLayer.data["I2"] > 32767):
            I2 += self.wattmeter.dataLayer.data["I2"] - 65535
        else:
            I2 += self.wattmeter.dataLayer.data["I2"]
            
        if (self.wattmeter.dataLayer.data["I3"] > 32767):
            I3 += self.wattmeter.dataLayer.data["I3"] - 65535
        else:
            I3 += self.wattmeter.dataLayer.data["I3"]

        if((I1 > I2)and(I1 > I3)):
            maxCurrent = math.ceil(I1/1000)

        if((I2 > I1)and(I2 > I3)):
            maxCurrent = math.ceil(I2/1000)
            
        if((I3 > I1)and(I3 > I2)):
            maxCurrent = math.ceil(I3/1000)
    
        delta = int(self.setting.config["sl,BREAKER"]) - maxCurrent

        # Kdyz je proud vetsi nez dvojnasobek proudu jsitice okamzite vypni a pak pockej 10s
        if ((maxCurrent < int(self.setting.config["sl,BREAKER"])  * 2) and (0 == self.__Delay_for_breaker)) :
            self.__cntCurrent = self.__cntCurrent+1
            #Dle normy je zmena proudu EV nasledujici po zmene pracovni cyklu PWM maximalne 5s
            if (self.__cntCurrent >= 3) :
                #self.stopTime = int(round(time.time() * 1000)) - self.startTime
                #print("Stop time: ",self.stopTime)
                #jestli je deltaBreaker zaporna a vetsi nez request current nastav request Current na 0
                if ((self.__requestCurrent + delta) < 0):
                    self.__requestCurrent = 0
                # jestli ze se nenabiji a nastavovany proud by byl vetsi nez je hodnota jistice, tak nastav proud na 0
                elif (self.dataLayer.data["EV_STATE"] != 3):
                    if ((self.__requestCurrent + maxCurrent) > int(self.setting.config["sl,BREAKER"])):
                        delta = 0
                        self.__requestCurrent = 0
                        #pri zahajeni nabijeni, je-li dostatek pvolneho proudu (>5A), tak nastavit porud na volnou deltu
                    if (delta > 5):
                        self.__requestCurrent  = 6

                else :
                    # kdyz proud presahne proud jistice, tak odecti deltu od nastavovaneho proudu
                    if (delta < 0):
                        self.__requestCurrent =  self.__requestCurrent + delta
                    else:
                        # kdyz je delta mensi nez 2A tak pricti deltu
                        if ((self.__requestCurrent + 1) <= int(self.setting.config["sl,BREAKER"])):
                            if (delta > 0) :
                                if(delta >= 6):
                                    self.__requestCurrent  = self.__requestCurrent + 2
                                else:
                                    self.__requestCurrent  = self.__requestCurrent + 1            
                        
                #self.startTime = int(round(time.time() * 1000))
                self.__cntCurrent = 0
        else:
            self.__requestCurrent = 0
            self.__Delay_for_breaker = self.__Delay_for_breaker+1
        if (self.__Delay_for_breaker > 60):
            self.__Delay_for_breaker = 0
        return  self.__requestCurrent
    
class DataLayer:
    def __init__(self):
        self.data = {}
        self.data["ACTUAL_CONFIG_CURRENT"] = 0
        self.data["ACTUAL_OUTPUT_CURRENT"] = 0
        self.data["EV_STATE"] = 0