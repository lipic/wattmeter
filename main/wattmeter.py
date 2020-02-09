from main import modbus
from machine import UART
import time
class Wattmeter:
     
    def __init__(self):
        try:
            self.uart = UART(2,115200)
            self.uart.init(115200,bits=8, parity=None, stop=1)
            self.modbusClient = modbus.Modbus()
            self.datalayer = Datalayer()
        
        except Exception as e:
             print(e)
             
    def updateData(self):
        try:
            receiveData = [50]
            readRegs = self.modbusClient.read_regs(1000, 20)
           # print(readRegs)
            self.uart.write(readRegs)
            time.sleep(0.01)
            #self.uart.readinto(receiveData)
            receiveData = self.uart.read()
            time.sleep(0.05)
            self.datalayer.data["E1"] =     (int)((((receiveData[5])) << 24) | ((receiveData[6])<< 16) | (((receiveData[3])) << 8) | ((receiveData[4])))
            self.datalayer.data["E2"] =     (int)((((receiveData[9])) << 24) | ((receiveData[10])<< 16) | (((receiveData[7])) << 8) | ((receiveData[8])))
            self.datalayer.data["E3"] =     (int)((((receiveData[13])) << 24) | ((receiveData[14])<< 16) | (((receiveData[11])) << 8) | ((receiveData[12])))
            self.datalayer.data["ESum"] =   (int)((((receiveData[17])) << 24) | ((receiveData[18])<< 16) | (((receiveData[15])) << 8) | ((receiveData[16])))
            self.datalayer.data["EFlash"] = (int)((((receiveData[21])) << 24) | ((receiveData[22])<< 16) | (((receiveData[19])) << 8) | ((receiveData[20])))
            self.datalayer.data["P1"] =     (int)((((receiveData[23])) << 8) | ((receiveData[24])))
            self.datalayer.data["P2"] =     (int)((((receiveData[25])) << 8) | ((receiveData[26])))
            self.datalayer.data["P3"] =     (int)((((receiveData[27])) << 8) | ((receiveData[28])))
            self.datalayer.data["PSum"] =   (int)((((receiveData[28])) << 8) | ((receiveData[30])))
            self.datalayer.data["I1"] =     (int)((((receiveData[31])) << 8) | ((receiveData[32])))
            self.datalayer.data["I2"] =     (int)((((receiveData[33])) << 8) | ((receiveData[34])))
            self.datalayer.data["I3"] =     (int)((((receiveData[35])) << 8) | ((receiveData[36])))
            self.datalayer.data["U1"] =     (int)((((receiveData[37])) << 8) | ((receiveData[38])))
            self.datalayer.data["U2"] =     (int)((((receiveData[39])) << 8) | ((receiveData[40])))
            self.datalayer.data["U3"] =     (int)((((receiveData[41])) << 8) | ((receiveData[42])))            

        except Exception as e:
            print(str(e))
        
class Datalayer:
    def __init__(self):
        self.data = {}
