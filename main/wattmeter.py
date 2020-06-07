from main import modbus
import machine
import time
import uasyncio as asyncio


class Wattmeter:
     
    def __init__(self,ID, timeout, baudrate , rxPin, txPin):
        
        self.uart = machine.UART(ID, baudrate=baudrate, rx=rxPin, tx=txPin)
        self.modbusClient = modbus.Modbus()
        self.dataLayer = DataLayer()
        self.fileHandler = fileHandler()
        self.MONTHLY_CONSUMPTION = 'monthly_consumption.dat'
        self.DAILY_CONSUMPTION = 'daily_consumption.dat'
        self.ntcShift = 2
        self.lastMinute =  int(time.localtime()[4])
        self.lastHour = int(time.localtime()[3])+2

    async def wattmeterHandler(self):
        #print("Minute: {}, Hour: ".format(self.lastMinute,self.lastHour))
        #Read data from wattmeter
        status = await self.__readWattmeter_data(1000,9)
        status = await self.__readWattmeter_data(2000,6)
        #status = await self.__readWattmeter_data(3000,3)
        status = await self.__readWattmeter_data(3102,1)
    
        #Check if time-sync puls must be send
        if(self.lastMinute is not int(time.localtime()[2])):
            status = await self.__writeWattmeter_data(100,1)
            self.lastMinute = int(time.localtime()[4])
            data = {("{}.{}.{}".format(time.localtime()[5],time.localtime()[1],time.localtime()[0])) : 10}
          #  self.fileHandler.handleData(self.DAILY_CONSUMPTION)
          #  self.fileHandler.writeData(self.DAILY_CONSUMPTION, data)
            
            
        if(self.lastHour is not int(time.localtime()[3]+self.ntcShift)):
            status = await self.__writeWattmeter_data(101,1)
            self.lastHour = int(time.localtime()[3]+self.ntcShift)
            print("Hour: ",self.lastHour)
        
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
                self.dataLayer.data["P1"] =     (int)((((receiveData[15])) << 8)  | ((receiveData[16])))
                self.dataLayer.data["P2"] =     (int)((((receiveData[17])) << 8)  | ((receiveData[18])))
                self.dataLayer.data["P3"] =     (int)((((receiveData[19])) << 8)  | ((receiveData[20])))
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

            elif (receiveData and (reg == 3102) and (0 == self.modbusClient.mbrtu_data_processing(receiveData))):
                
                self.dataLayer.data["E1_P"] =     (int)((((receiveData[3])) << 8)  | ((receiveData[4])))
             #   self.dataLayer.data["P2"] =     (int)((((receiveData[5])) << 8)  | ((receiveData[6])))
              #  self.dataLayer.data["P3"] =     (int)((((receiveData[7])) << 8)  | ((receiveData[8])))
                return "SUCCESS_READ"

            else: 
                return "Timed out waiting for result."
            
        except Exception as e:
            return "Exception: {}. UART is probably not connected.".format(e)
        
class DataLayer:
    def __init__(self):
        self.data = {}
        self.data["I1"] = 0
        self.data["I2"] = 0
        self.data["I3"] = 0
        self.data["U1"] = 0
        self.data["U2"] = 0
        self.data["U3"] = 0
        self.data["E1"] = 0
        self.data["E2"] = 0
        self.data["E3"] = 0
        self.data["P1"] = 0
        self.data["P2"] = 0
        self.data["P3"] = 0
        self.data["P24"] = []
        
class fileHandler:
            
    def handleData(self,file):
        try:
            data = self.readData(file)
        except OSError:
            return
        
        print(data)

        if(len(data)>3):

            print("Before: ",data)
            print("After: ",data[1:])
            
            lines = []
            for i in data:
                a,b = i.split(":")
                lines.append("{}:{}\n".format(a,b))
            with open(file, "w+") as f:
                lines = lines[1:]
                f.write(''.join(lines))
                f.close()

        
    def readData(self,file):
       # line = []
        data = [] 
        with open(file) as f:
            for line in f:
                line = line.replace("\n","")
                data.append(line)
             #   key, values = items[0], items[1]
             #   data[key] = values
            
            f.close()
        return data


    def writeData(self,file,data):
        lines = []
        for variable, value in data.items():
            lines.append("%s:%s\n" % (variable, value))
            
        with open(file, "a+") as f:
            f.write(''.join(lines))
            f.close()