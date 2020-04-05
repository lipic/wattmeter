from main import modbus
from machine import UART
import time
class Wattmeter:
     
    def __init__(self):
        
        self.uart = UART(2,115200)
        self.uart.init(115200,bits=8, parity=None, stop=1)
        self.modbusClient = modbus.Modbus()
        self.rmsLayer = RMSlayer()

              
    def updateData(self):
        try:
            readRegs = self.modbusClient.read_regs(1000, 6)
            self.uart.write(readRegs)
            time.sleep(0.01)
            receiveData = self.uart.read()
            time.sleep(0.05)
            #self.datalayer.data["E1"] =     (int)((((receiveData[5])) << 24) | ((receiveData[6])<< 16) | (((receiveData[3])) << 8) | ((receiveData[4])))
    
            self.rmsLayer.data["I1"] =     (int)((((receiveData[4])) << 8)  | ((receiveData[3])))
            self.rmsLayer.data["I2"] =     (int)((((receiveData[6])) << 8)  | ((receiveData[5])))
            self.rmsLayer.data["I3"] =     (int)((((receiveData[8])) << 8)  | ((receiveData[7])))
            self.rmsLayer.data["U1"] =     (int)((((receiveData[10])) << 8)  | ((receiveData[9])))
            self.rmsLayer.data["U2"] =     (int)((((receiveData[12])) << 8) | ((receiveData[11])))
            self.rmsLayer.data["U3"] =     (int)((((receiveData[14])) << 8) | ((receiveData[13])))
            return None

        except Exception as e:
            return "Exception: {}. UART is probably not connected.".format(e)
        
class RMSlayer:
    def __init__(self):
        self.data = {}
