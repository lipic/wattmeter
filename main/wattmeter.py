import time
import uasyncio as asyncio
from machine import Pin,UART
from main import __config__

class Wattmeter:
     
    def __init__(self,wattmeter):
        self.relay  = Pin(25, Pin.OUT)
        self.wattmeterInterface = wattmeter
        self.dataLayer = DataLayer()
        self.fileHandler = fileHandler()
        self.MONTHLY_CONSUMPTION = 'monthly_consumption.dat'
        self.DAILY_CONSUMPTION = 'daily_consumption.dat'
        self.timeInit = False
        self.timeOfset = False
        self.lastMinute =  0
        self.lastHour = 0
        self.lastDay =  0
        self.test = 0
        self.startUpTime = 0
        self.dataLayer.data['ID'] =__config__.Config().getConfig()['ID'] 

    async def wattmeterHandler(self):
        #Read data from wattmeter
        if((self.timeOfset == False)and (self.timeInit == True)):
            self.startUpTime = time.time()
            self.lastMinute =  int(time.localtime()[4])
            self.lastDay =  int(time.localtime()[2])
            self.dataLayer.data['DailyEnergy'] = self.fileHandler.readData(self.DAILY_CONSUMPTION)
            self.timeOfset = True
            
        self.dataLayer.data['RUN_TIME'] = time.time() - self.startUpTime
        curentYear = str(time.localtime()[0])[-2:] 
        self.dataLayer.data['WATTMETER_TIME'] = ("{0:02}.{1:02}.{2}  {3:02}:{4:02}:{5:02}".format(time.localtime()[2],time.localtime()[1],curentYear,time.localtime()[3],time.localtime()[4],time.localtime()[5]))
        #read U,I,P
        status = await self.__readWattmeter_data(1000,12)
        status = await self.__readWattmeter_data(2502,3)
        status = await self.__readWattmeter_data(2802,6)
        #Current Day consumption
        status = await self.__readWattmeter_data(3102,12)
        #Previous Day consumption
        status = await self.__readWattmeter_data(2902,6)
        #Power factor Day 
        status = await self.__readWattmeter_data(1015,3)
        #Total energy 
        status = await self.__readWattmeter_data(4000,12)
        #Total energy 
        status = await self.__readWattmeter_data(200,1)
        
        self.controlRelay()
        #Check if time-sync puls must be send
        if((self.lastMinute is not int(time.localtime()[4]))and(self.timeInit == True)):
            
            if(len(self.dataLayer.data["P_minuten"])<61):
                self.dataLayer.data["P_minuten"].append(self.dataLayer.data["Emin_Positive"]*6)#self.dataLayer.data["P1"])
            else:
                self.dataLayer.data["P_minuten"] = self.dataLayer.data["P_minuten"][1:]
                self.dataLayer.data["P_minuten"].append(self.dataLayer.data["Emin_Positive"]*6)#self.dataLayer.data["P1"])
            
            self.dataLayer.data["P_minuten"][0] = len(self.dataLayer.data["P_minuten"])
            status = await self.wattmeterInterface.writeWattmeterRegister(100,[1])
            self.lastMinute = int(time.localtime()[4]) 
            
        if(self.timeInit == True):
            if(self.lastHour is not int(time.localtime()[3])):
                status = await self.wattmeterInterface.writeWattmeterRegister(101,[1])
                self.lastHour = int(time.localtime()[3])
                if(len(self.dataLayer.data["E_hour"])<73):
                    self.dataLayer.data["E_hour"].append(self.lastHour)
                    self.dataLayer.data["E_hour"].append(self.dataLayer.data["Ehour_Positive"])
                    self.dataLayer.data["E_hour"].append(self.dataLayer.data["Ehour_Negative"])
                else:
                    self.dataLayer.data["E_hour"] = self.dataLayer.data["E_hour"][3:]
                    self.dataLayer.data["E_hour"].append(self.lastHour)
                    self.dataLayer.data["E_hour"].append(self.dataLayer.data["Ehour_Positive"])
                    self.dataLayer.data["E_hour"].append(self.dataLayer.data["Ehour_Negative"])
            
                self.dataLayer.data["E_hour"][0] = len(self.dataLayer.data["E_hour"])
            
        else:  
            if(len(self.dataLayer.data["E_hour"])<73):
                self.dataLayer.data["E_hour"][len(self.dataLayer.data["E_hour"])-2]= self.dataLayer.data["Ehour_Positive"]
                self.dataLayer.data["E_hour"][len(self.dataLayer.data["E_hour"])-1]= self.dataLayer.data["Ehour_Negative"]
            else:
                self.dataLayer.data["E_hour"][71]= self.dataLayer.data["Ehour_Positive"]
                self.dataLayer.data["E_hour"][72]= self.dataLayer.data["Ehour_Negative"]
        
            
        if((self.lastDay is not int(time.localtime()[2]))and(self.timeInit == True)):
            curentYear = str(time.localtime()[0])[-2:] 
            data = {("{0:02}/{1:02}/{2}".format(time.localtime()[1],self.lastDay ,curentYear)) : [self.dataLayer.data["E_currentDay_positive"], self.dataLayer.data["E_currentDay_negative"]]}
            status = await self.wattmeterInterface.writeWattmeterRegister(102,[1])
            self.lastDay = int(time.localtime()[2])
            self.fileHandler.handleData(self.DAILY_CONSUMPTION)
            self.fileHandler.writeData(self.DAILY_CONSUMPTION, data)
            self.dataLayer.data["DailyEnergy"] = self.fileHandler.readData(self.DAILY_CONSUMPTION) 
    
    async def __readWattmeter_data(self,reg,length):

        receiveData = await self.wattmeterInterface.readWattmeterRegister(reg,length)
       
        try:
            if ((receiveData != "Null") and (reg == 1000)):
                self.dataLayer.data["I1"] =     (int)((((receiveData[0])) << 8)  | ((receiveData[1])))
                self.dataLayer.data["I2"] =     (int)((((receiveData[2])) << 8)  | ((receiveData[3])))
                self.dataLayer.data["I3"] =     (int)((((receiveData[4])) << 8)  | ((receiveData[5])))
                self.dataLayer.data["U1"] =     (int)((((receiveData[6])) << 8)  | ((receiveData[7])))
                self.dataLayer.data["U2"] =     (int)((((receiveData[8])) << 8) | ((receiveData[9])))
                self.dataLayer.data["U3"] =     (int)((((receiveData[10])) << 8) | ((receiveData[11])))
                self.dataLayer.data["P1"] =     (int)((((receiveData[12])) << 8)  | ((receiveData[13])))
                self.dataLayer.data["P2"] =     (int)((((receiveData[14])) << 8)  | ((receiveData[15])))
                self.dataLayer.data["P3"] =     (int)((((receiveData[16])) << 8)  | ((receiveData[17])))
                self.dataLayer.data["S1"] =     (int)((((receiveData[18])) << 8)  | ((receiveData[19])))
                self.dataLayer.data["S2"] =     (int)((((receiveData[20])) << 8)  | ((receiveData[21])))
                self.dataLayer.data["S3"] =     (int)((((receiveData[22])) << 8)  | ((receiveData[23])))
     
                return "SUCCESS_READ"
                
            if ((receiveData != "Null") and (reg == 200)):
                self.dataLayer.data["HDO"] =     (int)((((receiveData[0])) << 8)  | ((receiveData[1])))
                
                return "SUCCESS_READ"
            
            elif ((receiveData != "Null") and (reg == 1015)):
                
                self.dataLayer.data["PF1"] = (int)((((receiveData[0])) << 8)  | ((receiveData[1])))
                self.dataLayer.data["PF2"] = (int)((((receiveData[2])) << 8)  | ((receiveData[3])))
                self.dataLayer.data["PF3"] = (int)((((receiveData[4])) << 8)  | ((receiveData[5])))
                return "SUCCESS_READ"
            
            elif ((receiveData != "Null") and (reg == 2502)):
                
                self.dataLayer.data["Emin_Positive"] =     (int)((((receiveData[0])) << 8)  | ((receiveData[1]))) + (int)((((receiveData[2])) << 8)  | ((receiveData[3]))) + (int)((((receiveData[4])) << 8)  | ((receiveData[5])))
                return "SUCCESS_READ"
             
            elif ((receiveData != "Null") and (reg == 2802)):
                
                self.dataLayer.data["Ehour_Positive"] =     (int)((((receiveData[0])) << 8)  | ((receiveData[1]))) + (int)((((receiveData[2])) << 8)  | ((receiveData[3]))) + (int)((((receiveData[4])) << 8)  | ((receiveData[5])))
                self.dataLayer.data["Ehour_Negative"] =     (int)((((receiveData[6])) << 8)  | ((receiveData[7]))) + (int)((((receiveData[8])) << 8)  | ((receiveData[9]))) + (int)((((receiveData[10])) << 8)  | ((receiveData[11])))
                return "SUCCESS_READ"

            elif ((receiveData != "Null") and (reg == 3102)):
                
                self.dataLayer.data["E_currentDay_positive"] =     (int)((((receiveData[0])) << 8)  | ((receiveData[1]))) + (int)((((receiveData[2])) << 8)  | ((receiveData[3]))) + (int)((((receiveData[4])) << 8)  | ((receiveData[5])))
                self.dataLayer.data["E_currentDay_negative"] =     (int)((((receiveData[6])) << 8)  | ((receiveData[7]))) + (int)((((receiveData[8])) << 8)  | ((receiveData[9]))) + (int)((((receiveData[10])) << 8)  | ((receiveData[11])))
                self.dataLayer.data["PP1_peak"] =     (int)((((receiveData[12])) << 8)  | ((receiveData[13])))
                self.dataLayer.data["PP2_peak"] =     (int)((((receiveData[14])) << 8)  | ((receiveData[15])))
                self.dataLayer.data["PP3_peak"] =     (int)((((receiveData[16])) << 8)  | ((receiveData[17])))
                self.dataLayer.data["PN1_peak"] =     (int)((((receiveData[18])) << 8)  | ((receiveData[19])))
                self.dataLayer.data["PN2_peak"] =     (int)((((receiveData[20])) << 8)  | ((receiveData[21]))) 
                self.dataLayer.data["PN3_peak"] =     (int)((((receiveData[22])) << 8)  | ((receiveData[23])))
                return "SUCCESS_READ"
                    
            elif ((receiveData != "Null") and (reg == 4000)):
                
                self.dataLayer.data["E1_total_positive"] =      (int)((receiveData[2] << 24) |  (receiveData[3] << 16) |  (receiveData[0] << 8)  | receiveData[1] )
                self.dataLayer.data["E2_total_positive"] =      (int)((receiveData[6] << 24) |  (receiveData[7] << 16) |  (receiveData[4] << 8)  | receiveData[5] )
                self.dataLayer.data["E3_total_positive"] =      (int)((receiveData[10] << 24) |  (receiveData[11] << 16) |  (receiveData[8] << 8)  | receiveData[9] )
                self.dataLayer.data["E1_total_negative"] =     (int)((receiveData[14] << 24) |  (receiveData[15] << 16) |  (receiveData[12] << 8)  | receiveData[13] )
                self.dataLayer.data["E2_total_negative"] =     (int)((receiveData[18] << 24) |  (receiveData[19] << 16) |  (receiveData[16] << 8)  | receiveData[17] )
                self.dataLayer.data["E3_total_negative"] =     (int)((receiveData[22] << 24) |  (receiveData[23] << 16) |  (receiveData[20] << 8)  | receiveData[21] )

                return "SUCCESS_READ"
            
            elif ((receiveData != "Null") and (reg == 2902)):
                
                self.dataLayer.data["E_previousDay_positive"] =     (int)((((receiveData[0])) << 8)  | ((receiveData[1]))) + (int)((((receiveData[2])) << 8)  | ((receiveData[3]))) + (int)((((receiveData[4])) << 8)  | ((receiveData[5])))
                self.dataLayer.data["E_previousDay_negative"] =     (int)((((receiveData[6])) << 8)  | ((receiveData[7]))) + (int)((((receiveData[8])) << 8)  | ((receiveData[9]))) + (int)((((receiveData[10])) << 8)  | ((receiveData[11])))
                return "SUCCESS_READ"

            else:  
                return "Timed out waiting for result."
            
        except Exception as e:
            return "Exception: {}. UART is probably not connected.".format(e)
        
    def negotiationRelay(self):
        if(self.relay.value()):
            self.relay.off()
            self.dataLayer.data["RELAY"]=0
            return False
        else:
            self.relay.on()
            self.dataLayer.data["RELAY"]=1
            return True
        
    def controlRelay(self):
        config = __config__.Config()
        if((config.getConfig()['sw,WHEN HDO: RELAY ON']) == '1'):
            if(self.dataLayer.data["HDO"] == 1):
                self.relay.on()
            else:
                self.relay.off()
        if(self.relay.value()):
            self.dataLayer.data["RELAY"]=1
        else:
            self.dataLayer.data["RELAY"]=0
        
class DataLayer:
    def __init__(self):
        self.data = {}
        self.data["I1"] = 0
        self.data["I2"] = 0
        self.data["I3"] = 0
        self.data["U1"] = 0
        self.data["U2"] = 0
        self.data["U3"] = 0
        self.data["PF1"] = 0
        self.data["PF2"] = 0
        self.data["PF3"] = 0 
        self.data["PP1_peak"] = 0
        self.data["PP2_peak"] = 0
        self.data["PP3_peak"] = 0
        self.data["PN1_peak"] = 0
        self.data["PN2_peak"] = 0
        self.data["PN3_peak"] = 0
        self.data["Emin_Positive"] = 0
        self.data["Ehour_Positive"] = 0
        self.data["Ehour_Negative"] = 0
        self.data["P1"] = 0
        self.data["P2"] = 0
        self.data["P3"] = 0
        self.data["S1"] = 0
        self.data["S2"] = 0
        self.data["S3"] = 0
        self.data["HDO"] = 0
        self.data["P_minuten"] = [0]
        self.data["E_hour"] = [0]
        self.data['DailyEnergy'] = None
        self.data["E_currentDay_positive"] = 0
        self.data["E_currentDay_negative"] = 0
        self.data["E_previousDay_positive"] = 0
        self.data["E_previousDay_negative"] = 0
        self.data["E1_total_positive"] = 0
        self.data["E2_total_positive"] = 0
        self.data["E3_total_positive"] = 0
        self.data["E1_total_negative"] = 0
        self.data["E2_total_negative"] = 0
        self.data["E3_total_negative"] = 0
        self.data['RUN_TIME'] = 0
        self.data['WATTMETER_TIME'] = 0
        self.data['ID'] = 0
         
class fileHandler:
            
    def handleData(self,file):
        try:
            data = self.readData(file)
        except OSError:
            return
        
        if(len(data)>30):
            lines = []
            for i in data:
                a,b = i.split(":")
                lines.append("{}:{}\n".format(a,b))
            with open(file, "w+") as f:
                lines = lines[1:]
                f.write(''.join(lines))
                f.close()

        
    def readData(self,file):

        data = []
        try:
            with open(file) as f:
                for line in f:
                    line = line.replace("\n","")
                    data.append(line)
            return data
        except Exception as e:
            return data 

    def writeData(self,file,data):
        lines = []
        for variable, value in data.items():
            lines.append("%s:%s\n" % (variable, value))
            
        with open(file, "a+") as f:
            f.write(''.join(lines))