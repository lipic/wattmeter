from main import modbus
import machine
import time
class Wattmeter:
     
    def __init__(self):
        
        self.uart = machine.UART(1, baudrate=115200, rx=26, tx=27)
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
    
            self.rmsLayer.data["I1"] =     (int)((((receiveData[3])) << 8)  | ((receiveData[4])))
            self.rmsLayer.data["I2"] =     (int)((((receiveData[5])) << 8)  | ((receiveData[6])))
            self.rmsLayer.data["I3"] =     (int)((((receiveData[7])) << 8)  | ((receiveData[8])))
            self.rmsLayer.data["U1"] =     (int)((((receiveData[9])) << 8)  | ((receiveData[10])))
            self.rmsLayer.data["U2"] =     (int)((((receiveData[11])) << 8) | ((receiveData[12])))
            self.rmsLayer.data["U3"] =     (int)((((receiveData[13])) << 8) | ((receiveData[14])))
            return None

        except Exception as e:
            return "Exception: {}. UART is probably not connected.".format(e)
        
class RMSlayer:
    def __init__(self):
        self.data = {}
