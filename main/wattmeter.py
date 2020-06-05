from main import modbus
import machine
import time
import uasyncio as asyncio


class Wattmeter:
     
    def __init__(self,ID, timeout, baudrate , rxPin, txPin):
        
        self.uart = machine.UART(ID, baudrate=baudrate, rx=rxPin, tx=txPin)
        self.modbusClient = modbus.Modbus()
        self.dataLayer = DataLayer()
        self.lastMinute = 0
        self.lastHour = 0
        self.ntcShift = 2

    async def wattmeterHandler(self):
        status = await self.__readWattmeter_data(1000,6)
        status = await self.__readWattmeter_data(2000,6)
        status = await self.__readWattmeter_data(3000,3)
    

        if(self.lastMinute is not int(time.localtime()[4])):
            status = await self.__writeWattmeter_data(100,1)
            self.lastMinute = int(time.localtime()[4])
            print("Minute: ",self.lastMinute)
        if(self.lastHour is not int(time.localtime()[3]+self.ntcShift)):
            status = await self.__writeWattmeter_data(101,1)
            self.lastHour = int(time.localtime()[3]+self.ntcShift)
            print("Hour: ",self.lastHour)

    def checkCurrentTime(self,val):
        print(int(time.localtime()[val]))
        if(self.lastMinute is not int(time.localtime()[3])):
           # status = await self.__writeWattmeter_data(100,1)
            self.lastMinute = int(time.localtime()[val])
            print("jsem tu")
            #print("New minuten {}".format(self.lastMinute))
            
        if(self.lastMinute != int(time.localtime()[3])):
            status = await self.__writeWattmeter_data(101,1)
            self.lastMinute = time.localtime()[3]
            print("New minuten {}".format(self.lastHour))
       
        
    async def __writeWattmeter_data(self,reg,data):
        writeRegs = self.modbusClient.write_regs(reg, [int(data)])
        self.uart.write(writeRegs)
        await asyncio.sleep(0.1)
        receiveData = self.uart.read()
        try:
            receiveData = receiveData[1:]
            if (0 == self.modbusClient.mbrtu_data_processing(receiveData)):
                return  'SUCCESS_WRITE'
            else:
                return 'ERROR'
        except Exception as e:
            return "Exception: {}".format(e)
        
    async def __readWattmeter_data(self,reg,length):
        readRegs = self.modbusClient.read_regs(reg, length)
        self.uart.write(readRegs)
        await asyncio.sleep(0.1)
        receiveData = self.uart.read()  

        try:
            if (receiveData and (reg == 1000) and  (0 == self.modbusClient.mbrtu_data_processing(receiveData))):

                self.dataLayer.data["I1"] =     (int)((((receiveData[3])) << 8)  | ((receiveData[4])))
                self.dataLayer.data["I2"] =     (int)((((receiveData[5])) << 8)  | ((receiveData[6])))
                self.dataLayer.data["I3"] =     (int)((((receiveData[7])) << 8)  | ((receiveData[8])))
                self.dataLayer.data["U1"] =     (int)((((receiveData[9])) << 8)  | ((receiveData[10])))
                self.dataLayer.data["U2"] =     (int)((((receiveData[11])) << 8) | ((receiveData[12])))
                self.dataLayer.data["U3"] =     (int)((((receiveData[13])) << 8) | ((receiveData[14])))
                return "SUCCESS_READ"
                
            
            elif (receiveData and (reg == 2000) and (0 == self.modbusClient.mbrtu_data_processing(receiveData))):
                
                self.dataLayer.data["E1"] =     (float)(((receiveData[5]) << 24) | ((receiveData[6])<< 16) | (((receiveData[3])) << 8) | ((receiveData[4])))
                self.dataLayer.data["E2"] =     (float)(((receiveData[9]) << 24) | ((receiveData[10])<< 16) | (((receiveData[7])) << 8) | ((receiveData[8])))
                self.dataLayer.data["E3"] =     (float)(((receiveData[13]) << 24) | ((receiveData[14])<< 16) | (((receiveData[11])) << 8) | ((receiveData[12])))
                return "SUCCESS_READ"
            
            elif (receiveData and (reg == 3000) and (0 == self.modbusClient.mbrtu_data_processing(receiveData))):
                
                self.dataLayer.data["P1"] =     (int)((((receiveData[3])) << 8)  | ((receiveData[4])))
                self.dataLayer.data["P2"] =     (int)((((receiveData[5])) << 8)  | ((receiveData[6])))
                self.dataLayer.data["P3"] =     (int)((((receiveData[7])) << 8)  | ((receiveData[8])))
                return "SUCCESS_READ"
                
            else: 
                return "Timed out waiting for result."
            
        except Exception as e:
            return "Exception: {}. UART is probably not connected.".format(e)
        
class DataLayer:
    def __init__(self):
        self.data = {}
        
