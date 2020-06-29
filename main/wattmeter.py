from main import modbus
import machine
import time
import uasyncio as asyncio


class Wattmeter:
     
    def __init__(self,lock ,ID, timeout, baudrate , rxPin, txPin):
        self.lock = lock
        self.uart = machine.UART(ID, baudrate=baudrate, rx=rxPin, tx=txPin)
        self.modbusClient = modbus.Modbus()
        self.dataLayer = DataLayer()
        self.fileHandler = fileHandler()
        self.MONTHLY_CONSUMPTION = 'monthly_consumption.dat'
        self.DAILY_CONSUMPTION = 'daily_consumption.dat'
        self.ntcShift = 2
        self.timeInit = False
        self.lastMinute =  0
        self.lastHour = 0
        self.lastDay =  0
        self.test = 0

    async def wattmeterHandler(self):
        #print("Minute: {}, Hour: ".format(self.lastMinute,self.lastHour))
        #Read data from wattmeter
        if(self.timeInit == False):
            self.lastMinute =  int(time.localtime()[4])
            #self.lastHour = int(time.localtime()[3])+2
            self.lastDay =  int(time.localtime()[2])
            self.timeInit = True
        
        #read U,I,P
        status = await self.__readWattmeter_data(1000,9)
        status = await self.__readWattmeter_data(2502,3)
        status = await self.__readWattmeter_data(2802,3)
        #Current Day consumption
        status = await self.__readWattmeter_data(3102,6)
        #Previous Day consumption
        status = await self.__readWattmeter_data(2902,6)
        #Previous Day consumption
        #status = await self.__readWattmeter_data(2902,6)
        
        #Check if time-sync puls must be send
        if(self.lastMinute is not int(time.localtime()[4])):
            
            if(len(self.dataLayer.data["P_minuten"])<61):
                self.dataLayer.data["P_minuten"].append(self.dataLayer.data["Emin_Positive"]*6)#self.dataLayer.data["P1"])
            else:
                self.dataLayer.data["P_minuten"] = self.dataLayer.data["P_minuten"][1:]
                self.dataLayer.data["P_minuten"].append(self.dataLayer.data["Emin_Positive"]*6)#self.dataLayer.data["P1"])
            
            self.dataLayer.data["P_minuten"][0] = len(self.dataLayer.data["P_minuten"])
            status = await self.writeWattmeterRegister(100,[1])
            self.lastMinute = int(time.localtime()[4])

        
            
            
        if(self.lastHour is not int(time.localtime()[3]+self.ntcShift)):
            status = await self.writeWattmeterRegister(101,[1])
            self.lastHour = int(time.localtime()[3])+self.ntcShift
            
            if(len(self.dataLayer.data["E_hour"])<49):
                self.dataLayer.data["E_hour"].append(self.lastHour)
                self.dataLayer.data["E_hour"].append(self.dataLayer.data["Ehour_Positive"])
            else:
                self.dataLayer.data["E_hour"] = self.dataLayer.data["E_hour"][2:]
                self.dataLayer.data["E_hour"].append(self.lastHour)
                self.dataLayer.data["E_hour"].append(self.dataLayer.data["Ehour_Positive"])
            
            self.dataLayer.data["E_hour"][0] = len(self.dataLayer.data["E_hour"])
            
        else:
            if(len(self.dataLayer.data["E_hour"])<49):
                self.dataLayer.data["E_hour"][len(self.dataLayer.data["E_hour"])-1]= self.dataLayer.data["Ehour_Positive"]
                print("Zapisuji: ",self.dataLayer.data["E_hour"])
            else:
                self.dataLayer.data["E_hour"][49]= self.dataLayer.data["Ehour_Positive"]

            
        if(self.lastDay is not int(time.localtime()[2])):
            status = await self.writeWattmeterRegister(102,[1])
            data = {("{}.{}.{}".format(time.localtime()[2],time.localtime()[1],time.localtime()[0])) : 20}
            print("New day",self.lastDay )
            self.lastDay = int(time.localtime()[2])
            #self.fileHandler.handleData(self.DAILY_CONSUMPTION)
            #self.fileHandler.writeData(self.DAILY_CONSUMPTION, data)
     
         
    async def writeWattmeterRegister(self,reg,data):
        await self.lock.acquire()
        writeRegs = self.modbusClient.write_regs(reg, data)
        self.uart.write(writeRegs)
        await asyncio.sleep_ms(50)
        receiveData = self.uart.read()
        self.lock.release()
        try:
            if (0 == self.modbusClient.mbrtu_data_processing(receiveData)):
                data = bytearray()
                data.append(receiveData[2])
                data.append(receiveData[3])
                return data
            else:
                return 'ERROR'
        except Exception as e:
            return "Exception: {}".format(e)
    
        
    async def readWattmeterRegister(self,reg,length):
        await self.lock.acquire()
        readRegs = self.modbusClient.read_regs(reg, length)
        self.uart.write(readRegs)
        await asyncio.sleep_ms(50)
        receiveData = self.uart.read()
        self.lock.release()
        try:
            if (receiveData  and  (0 == self.modbusClient.mbrtu_data_processing(receiveData))):
                data = bytearray()
                for i in range(0,(length*2)):
                    data.append(receiveData[i+3])
                return data
            else:
                return "Null"
        except Exception as e:
            return "Error"
    
    
    async def __readWattmeter_data(self,reg,length):

        receiveData = await self.readWattmeterRegister(reg,length)
       
        try:
            if ((receiveData != "Null" and receiveData != "Error") and (reg == 1000)):
                self.dataLayer.data["I1"] =     (int)((((receiveData[0])) << 8)  | ((receiveData[1])))
                self.dataLayer.data["I2"] =     (int)((((receiveData[2])) << 8)  | ((receiveData[3])))
                self.dataLayer.data["I3"] =     (int)((((receiveData[4])) << 8)  | ((receiveData[5])))
                self.dataLayer.data["U1"] =     (int)((((receiveData[6])) << 8)  | ((receiveData[7])))
                self.dataLayer.data["U2"] =     (int)((((receiveData[8])) << 8) | ((receiveData[9])))
                self.dataLayer.data["U3"] =     (int)((((receiveData[10])) << 8) | ((receiveData[11])))
                self.dataLayer.data["P1"] =     (int)((((receiveData[12])) << 8)  | ((receiveData[13])))
                self.dataLayer.data["P2"] =     (int)((((receiveData[14])) << 8)  | ((receiveData[15])))
                self.dataLayer.data["P3"] =     (int)((((receiveData[16])) << 8)  | ((receiveData[17])))
                
                return "SUCCESS_READ"
                
            
            elif ((receiveData != "Null" and receiveData != "Error") and (reg == 2502)):
                
                self.dataLayer.data["Emin_Positive"] =     (int)((((receiveData[0])) << 8)  | ((receiveData[1]))) + (int)((((receiveData[2])) << 8)  | ((receiveData[3]))) + (int)((((receiveData[4])) << 8)  | ((receiveData[5])))
                return "SUCCESS_READ"
             
            elif ((receiveData != "Null" and receiveData != "Error") and (reg == 2802)):
                
                self.dataLayer.data["Ehour_Positive"] =     (int)((((receiveData[0])) << 8)  | ((receiveData[1]))) + (int)((((receiveData[2])) << 8)  | ((receiveData[3]))) + (int)((((receiveData[4])) << 8)  | ((receiveData[5])))
                self.dataLayer.data["Ehour_Negative"] =     (int)((((receiveData[6])) << 8)  | ((receiveData[7]))) + (int)((((receiveData[8])) << 8)  | ((receiveData[9]))) + (int)((((receiveData[10])) << 8)  | ((receiveData[11])))
                return "SUCCESS_READ"

            elif ((receiveData != "Null" and receiveData != "Error") and (reg == 3102)):
                
                self.dataLayer.data["E_currentDay_positive"] =     (int)((((receiveData[0])) << 8)  | ((receiveData[1]))) + (int)((((receiveData[2])) << 8)  | ((receiveData[3]))) + (int)((((receiveData[4])) << 8)  | ((receiveData[5])))
                self.dataLayer.data["E_currentDay_negative"] =     (int)((((receiveData[6])) << 8)  | ((receiveData[7]))) + (int)((((receiveData[8])) << 8)  | ((receiveData[9]))) + (int)((((receiveData[10])) << 8)  | ((receiveData[11])))
                return "SUCCESS_READ"
            
            elif ((receiveData != "Null" and receiveData != "Error") and (reg == 2902)):
                
                self.dataLayer.data["E_previousDay_positive"] =     (int)((((receiveData[0])) << 8)  | ((receiveData[1]))) + (int)((((receiveData[2])) << 8)  | ((receiveData[3]))) + (int)((((receiveData[4])) << 8)  | ((receiveData[5])))
                self.dataLayer.data["E_previousDay_negative"] =     (int)((((receiveData[6])) << 8)  | ((receiveData[7]))) + (int)((((receiveData[8])) << 8)  | ((receiveData[9]))) + (int)((((receiveData[10])) << 8)  | ((receiveData[11])))
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
        self.data["Emin_Positive"] = 0
        self.data["Ehour_Positive"] = 0
        self.data["P1"] = 0
        self.data["P2"] = 0
        self.data["P3"] = 0
        self.data["P_minuten"] = [0]
        self.data["E_hour"] = [0]
        self.data["E_currentDay_positive"] = 0
        self.data["E_currentDay_negative"] = 0
        self.data["E_previousDay_positive"] = 0
        self.data["E_previousDay_negative"] = 0
        
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