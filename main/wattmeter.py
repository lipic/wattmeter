from main import modbus
import machine
import time
import uasyncio as asyncio


class Wattmeter:
     
    def __init__(self,ID, timeout, baudrate , rxPin, txPin):
        
        self.uart = machine.UART(ID, baudrate=baudrate, rx=rxPin, tx=txPin)
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

                self.dataLayer.data["I1"] =     (int)((((self.receiveData[3])) << 8)  | ((self.receiveData[4])))
                self.dataLayer.data["I2"] =     (int)((((self.receiveData[5])) << 8)  | ((self.receiveData[6])))
                self.dataLayer.data["I3"] =     (int)((((self.receiveData[7])) << 8)  | ((self.receiveData[8])))
                self.dataLayer.data["U1"] =     (int)((((self.receiveData[9])) << 8)  | ((self.receiveData[10])))
                self.dataLayer.data["U2"] =     (int)((((self.receiveData[11])) << 8) | ((self.receiveData[12])))
                self.dataLayer.data["U3"] =     (int)((((self.receiveData[13])) << 8) | ((self.receiveData[14])))    
                
            
            elif (self.receiveData and (reg == 2000)):
                
                self.dataLayer.data["E1"] =     (float)(((self.receiveData[5]) << 24) | ((self.receiveData[6])<< 16) | (((self.receiveData[3])) << 8) | ((self.receiveData[4])))
                self.dataLayer.data["E2"] =     (float)(((self.receiveData[9]) << 24) | ((self.receiveData[10])<< 16) | (((self.receiveData[7])) << 8) | ((self.receiveData[8])))
                self.dataLayer.data["E3"] =     (float)(((self.receiveData[13]) << 24) | ((self.receiveData[14])<< 16) | (((self.receiveData[11])) << 8) | ((self.receiveData[12])))
                return "{}".format(self.receiveData[3],self.receiveData[4],self.receiveData[5],self.receiveData[6])
            
            elif (self.receiveData and (reg == 3000)):
                
                self.dataLayer.data["P1"] =     (int)((((self.receiveData[3])) << 8)  | ((self.receiveData[4])))
                self.dataLayer.data["P2"] =     (int)((((self.receiveData[5])) << 8)  | ((self.receiveData[6])))
                self.dataLayer.data["P3"] =     (int)((((self.receiveData[7])) << 8)  | ((self.receiveData[8])))
                
            else: 
                return "Timed out waiting for result."
            
        except Exception as e:
            return "Exception: {}. UART is probably not connected.".format(e)
        
class DataLayer:
    def __init__(self):
        self.data = {}
        
