from main import modbus
from machine import UART
import uasyncio as asyncio
from machine import Pin
import time

class Evse():

    
    def __init__(self,baudrate ):
        self.DE = Pin(15, Pin.OUT) 
        #self.uart = UART(2)
        self.uart =  UART(2,baudrate, bits=8, parity=None)
        #self.uart = machine.UART(2, baudrate=baudrate)
        self.modbusClient = modbus.Modbus()
        self.dataLayer = DataLayer()
        self.receiveData = []
        
       # self.setting = setting
        

    def __readRegs(self,reg,length):
        readRegs = self.modbusClient.read_regs(reg, length)
        self.uart.write(readRegs)

    def __recvData(self):
        self.receiveData = []
        self.receiveData = self.uart.read() 
    
    async def update_Data(self,reg,length):
        self.DE.off()
        self.__readRegs(reg,length)
        #await asyncio.sleep(0.01)
        self.DE.on()
        #await asyncio.sleep(0.2) 
        self. __recvData()
        await asyncio.sleep(0.1)
        
        try:
            if(self.receiveData):
                self.receiveData = self.receiveData[1:]
                result = self.modbusClient.mbrtu_data_processing(self.receiveData)
                
                if (reg == 1000):
                    self.dataLayer.data["EVSE1"] =     (int)((((self.receiveData[4])) << 8)  | ((self.receiveData[5])))
                    self.dataLayer.data["EVSE2"] =     (int)((((self.receiveData[6])) << 8)  | ((self.receiveData[7])))
                    self.dataLayer.data["EVSE3"] =     (int)((((self.receiveData[8])) << 8)  | ((self.receiveData[9])))
                    return "Data from wattmeter address: {}, result:{}, data:{} were received. Result: ".format(reg,result)
                        
                else: 
                    return "Timed out waiting for result."
            
        except Exception as e:
            print(e)
            return "Exception: {}. UART is probably not connected.".format(e)
        
class DataLayer:
    def __init__(self):
        self.data = {}