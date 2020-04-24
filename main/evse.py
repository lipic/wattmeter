from main import modbus
from machine import UART
import uasyncio as asyncio


class Evse:
     
    def __init__(self,baudrate ):
        
        self.uart = UART(2, 115200)
        self.uart.init(115200, bits=8, parity=None, stop=1) 
        self.modbusClient = modbus.Modbus()
        self.dataLayer = DataLayer()
        self.receiveData = [] 
       # self.setting = setting
        
        
    def __readRegs(self,reg,length):
        self.receiveData = []
        readRegs = self.modbusClient.read_regs(reg, length)
        self.uart.write(readRegs)

    def __recvData(self):
        self.receiveData = self.uart.read()  
    
    async def update_Data(self,reg,length):
        self.__readRegs(reg,length)
        await asyncio.sleep(0.2)
        self. __recvData() 
        
        try:
            if (self.receiveData and (reg == 1000)):

                self.dataLayer.data["EVSE1"] =     (int)((((self.receiveData[3])) << 8)  | ((self.receiveData[4])))
                self.dataLayer.data["EVSE2"] =     (int)((((self.receiveData[5])) << 8)  | ((self.receiveData[6])))
                self.dataLayer.data["EVSE3"] =     (int)((((self.receiveData[7])) << 8)  | ((self.receiveData[8])))
                return "Data: {} from wattmeter address: {} were received.".format(self.receiveData,reg)
                        
            else: 
                return "Timed out waiting for result."
            
        except Exception as e:
            return "Exception: {}. UART is probably not connected.".format(e)
        
class DataLayer:
    def __init__(self):
        self.data = {}