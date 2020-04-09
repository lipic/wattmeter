from main import modbus
import machine
import time
import uasyncio as asyncio


class Wattmeter:
     
    def __init__(self,ID, timeout, baudrate , rxPin, txPin):
        
        self.uart = machine.UART(ID, baudrate=baudrate, rx=rxPin, tx=txPin)
        self.modbusClient = modbus.Modbus()
        self.rmsLayer = RMSlayer()
        self.swriter = asyncio.StreamWriter(self.uart, {})
        self.sreader = asyncio.StreamReader(self.uart)
        self.receiveData = []

    async def readRegs(self,reg,length):
        self.receiveData = []
        readRegs = self.modbusClient.read_regs(reg, length)
        self.swriter.awrite(readRegs)
        await asyncio.sleep(0.1)
        self._recv() 
        

    def _recv(self):
        res = self.sreader.readline()
        self.receiveData.append(res)
            #await asyncio.sleep(0.1)
    
    def updateData(self):

        try:
            if self.receiveData:
                #self.datalayer.data["E1"] =     (int)((((receiveData[5])) << 24) | ((receiveData[6])<< 16) | (((receiveData[3])) << 8) | ((receiveData[4])))
                self.rmsLayer.data["I1"] =     (int)((((self.receiveData[3])) << 8)  | ((self.receiveData[4])))
                self.rmsLayer.data["I2"] =     (int)((((self.receiveData[5])) << 8)  | ((self.receiveData[6])))
                self.rmsLayer.data["I3"] =     (int)((((self.receiveData[7])) << 8)  | ((self.receiveData[8])))
                self.rmsLayer.data["U1"] =     (int)((((self.receiveData[9])) << 8)  | ((self.receiveData[10])))
                self.rmsLayer.data["U2"] =     (int)((((self.receiveData[11])) << 8) | ((self.receiveData[12])))
                self.rmsLayer.data["U3"] =     (int)((((self.receiveData[13])) << 8) | ((self.receiveData[14])))
            
                return "Transmition complete."

            else: 
                return "Timed out waiting for result."
            
        except Exception as e:
            return "Exception: {}. UART is probably not connected.".format(e)
        
class RMSlayer:
    def __init__(self):
        self.data = {}
