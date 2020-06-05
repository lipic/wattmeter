from main import modbus
from machine import UART
import uasyncio as asyncio
from machine import Pin
import time

class Evse():

    
    def __init__(self,baudrate, setting,wattmeter):
        self.DE = Pin(15, Pin.OUT) 
        self.uart =  UART(2,baudrate, bits=8, parity=None)
        self.modbusClient = modbus.Modbus()
        self.dataLayer = DataLayer()
        self.receiveData = []
        self.setting = setting
        self.wattmeter = wattmeter
        self.__Delay_for_breaker = 0
        self.__cntCurrent = 0
        self.__requestCurrent = 0
        
       # self.setting = setting

    
    async def evseHandler(self):
        #first read data from evse
        current = 0
        state = "1"
        status = await self.__readEvse_data(1000,3)
        if(status == 'SUCCESS'):
            #If get max current accordig to wattmeter
            if(self.setting.config["sw,Enable charging"] == 'True'):
                if (self.setting.config["sw,Enable balancing"] == 'True'):
                    current = self.balancEvseCurrent()
                    state = await self.__writeEvse_data(1000,current)
                else:
                    current = self.setting.config["sl,Breaker"]
                    state = await self.__writeEvse_data(1000,current)

            else: 
                current = 0
                
            print("main Breaker: ",self.setting.config["sl,Breaker"])
            print("Evse current: ",current)
        
        return "Read: {}; Write: {}".format(status,state)
     
    async def __writeEvse_data(self,reg,data):
        self.DE.off()
        writeRegs = self.modbusClient.write_regs(reg, [int(data)])
        self.uart.write(writeRegs)
        self.DE.on()
        self.receiveData = []
        self.receiveData = self.uart.read() 
        await asyncio.sleep(0.1)
        return "SUCCESS"

 
        
    async def __readEvse_data(self,reg,length):
        self.DE.off()
        readRegs = self.modbusClient.read_regs(reg, length)
        self.uart.write(readRegs)
        self.DE.on()
        self.receiveData = []
        self.receiveData = self.uart.read() 
        await asyncio.sleep(0.1)

        try:
            if(self.receiveData):
                self.receiveData = self.receiveData[1:]
                    
                if ((reg == 1000)and (0 == self.modbusClient.mbrtu_data_processing(self.receiveData))):
                    self.dataLayer.data["ACTUAL_CONFIG_CURRENT"] =     (int)((((self.receiveData[3])) << 8)  | ((self.receiveData[4])))
                    self.dataLayer.data["ACTUAL_OUTPUT_CURRENT"] =     (int)((((self.receiveData[5])) << 8)  | ((self.receiveData[6])))
                    self.dataLayer.data["EV_STATE"] =     (int)((((self.receiveData[7])) << 8)  | ((self.receiveData[8])))
                    return "Read data: {}".format(self.dataLayer.data)
                        
                else: 
                    return "Timed out waiting for result."
                 
  
        except Exception as e:
            return "Exception: {} Data:{}".format(e, self.receiveData)
        

    def balancEvseCurrent(self):
        #Zjisti deltu
        import random
        maxCurrent = self.__requestCurrent + random.randint(1,16)#self.dataLayer.data["I1"]  + self.dataLayer.data["I2"]  + self.dataLayer.data["I3"]

        delta = int(self.setting.config["sl,Breaker"]) - maxCurrent
        # Kdyz je proud vetsi nez dvojnasobek proudu jsitice okamzite vypni a pak pockej 10s
        if ((maxCurrent < int(self.setting.config["sl,Breaker"])  * 2) and (0 == self.__Delay_for_breaker)) :
            self.__cntCurrent = self.__cntCurrent+1
            #Dle normy je zmena proudu EV nasledujici po zmene pracovni cyklu PWM maximalne 5s
            if (self.__cntCurrent >= 5) :
                #jestli je deltaBreaker zaporna a vetsi nez request current nastav request Current na 0
                if ((self.__requestCurrent + delta) < 0):
                    self.__requestCurrent = 0
                # jestli ze se nenabiji a nastavovany proud by byl vetsi nez je hodnota jistice, tak nastav proud na 0
                elif (self.dataLayer.data["EV_STATE"] != 3):
                    if ((self.__requestCurrent + maxCurrent) > int(self.setting.config["sl,Breaker"])):
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
                        if ((self.__requestCurrent + 1) <= int(self.setting.config["sl,Breaker"])):
                            if (delta > 0) :
                                if(delta >= 6):
                                    self.__requestCurrent  = self.__requestCurrent + 2
                                else:
                                    self.__requestCurrent  = self.__requestCurrent + 1            
                
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