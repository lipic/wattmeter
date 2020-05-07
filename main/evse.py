from main import modbus
import machine
import uasyncio as asyncio
from machine import Pin
import time
import io 
import rs485

class Evse(io.IOBase):

    
    def __init__(self,baudrate ):
       # self.DE = Pin(15, Pin.OUT) 
     #   self.uart = UART(2)
        #self.uart = machine.UART(2,baudrate, bits=8, parity=None,rx=16 tx=17,rts=15)
        self.uart = machine.UART(2, baudrate=baudrate, rts=15)
        self.modbusClient = modbus.Modbus()
        self.dataLayer = DataLayer()
        self.receiveData = [] 
       # self.setting = setting
        

    def __readRegs(self,reg,length):
        readRegs = self.modbusClient.read_regs(reg, length)
        a = self.uart.write(readRegs)

            

    def __recvData(self):
        self.receiveData = []
        self.receiveData = self.uart.read() 
    
    def update_Data(self,reg,length):
       # self.DE.off()
        self.__readRegs(reg,length)
        #await asyncio.sleep(0.01)
       # self.DE.on()
        #await asyncio.sleep(0.2) 
        self. __recvData()
       # await asyncio.sleep(0.2)
        time.sleep(0.1)
        print(self.receiveData)
        try:
            if (self.receiveData and (reg == 1000)):

                self.dataLayer.data["EVSE1"] =     (int)((((self.receiveData[4])) << 8)  | ((self.receiveData[5])))
                self.dataLayer.data["EVSE2"] =     (int)((((self.receiveData[6])) << 8)  | ((self.receiveData[7])))
                self.dataLayer.data["EVSE3"] =     (int)((((self.receiveData[8])) << 8)  | ((self.receiveData[9])))
                print(self.receiveData)
                print(self.dataLayer.data["EVSE1"] )
                print(self.dataLayer.data["EVSE2"] )
                print(self.dataLayer.data["EVSE3"] )
                return "Data from wattmeter address: {} were received.".format(reg)
                        
            else: 
                return "Timed out waiting for result."
            
        except Exception as e:
            return "Exception: {}. UART is probably not connected.".format(e)
        
class DataLayer:
    def __init__(self):
        self.data = {}