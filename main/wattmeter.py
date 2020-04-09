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
        loop = asyncio.get_event_loop()
        loop.create_task(self._recv())

    def readRegs(self,reg,length):
        self.receiveData = []
        readRegs = self.modbusClient.read_regs(reg, length)
        self.swriter.awrite(readRegs)
        print(readRegs)


    async def _recv(self):
        while True:
            res = await self.sreader.readline()
            self.receiveData.append(res)
            self.updateData()
    
    def updateData(self):

        try:
            print(self.receiveData)
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
                print("Timed out waiting for result.")
                return "Timed out waiting for result."
            
        except Exception as e:
            print("Exception: {}. UART is probably not connected.".format(e))
            return "Exception: {}. UART is probably not connected.".format(e)
        
class RMSlayer:
    def __init__(self):
        self.data = {}
