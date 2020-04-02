from main import modbus
from machine import UART
import time
class Wattmeter:
     
    def __init__(self):
        
        self.uart = UART(2,115200)
        self.uart.init(115200,bits=8, parity=None, stop=1)
        self.modbusClient = modbus.Modbus()
        self.datalayer = Datalayer()

              
    def updateData(self):
        try:
            receiveData = [50]
            readRegs = self.modbusClient.read_regs(1000, 6)
            self.uart.write(readRegs)
            time.sleep(0.01)
            receiveData = self.uart.read()
            time.sleep(0.05)
            #self.datalayer.data["E1"] =     (int)((((receiveData[5])) << 24) | ((receiveData[6])<< 16) | (((receiveData[3])) << 8) | ((receiveData[4])))
    
            self.datalayer.data["I1"] =     (int)((((receiveData[3])) << 8)  | ((receiveData[4])))
            self.datalayer.data["I2"] =     (int)((((receiveData[5])) << 8)  | ((receiveData[6])))
            self.datalayer.data["I3"] =     (int)((((receiveData[7])) << 8)  | ((receiveData[8])))
            self.datalayer.data["U1"] =     (int)((((receiveData[9])) << 8)  | ((receiveData[10])))
            self.datalayer.data["U2"] =     (int)((((receiveData[11])) << 8) | ((receiveData[12])))
            self.datalayer.data["U3"] =     (int)((((receiveData[13])) << 8) | ((receiveData[14])))

        except Exception as e:
            print(str(e))
        
class Datalayer:
    def __init__(self):
        self.data = {}
