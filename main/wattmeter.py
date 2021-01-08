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
        self.lastMounth = 0
        self.lastYear = 0
        self.test = 0
        self.startUpTime = 0
        self.dataLayer.data['ID'] =__config__.Config().getConfig()['ID'] 

    async def wattmeterHandler(self):
        #Read data from wattmeter
        if (self.timeOfset == False)and(self.timeInit == True):
            self.startUpTime = time.time()
            self.lastMinute =  int(time.localtime()[4])
            self.lastDay =  int(time.localtime()[2])
            self.lastMounth = int(time.localtime()[1])
            self.lastYear =  int(time.localtime()[0])
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
        if (self.lastMinute is not int(time.localtime()[4]))and(self.timeInit == True):
            
            if len(self.dataLayer.data["P_minuten"])<61:
                self.dataLayer.data["P_minuten"].append(self.dataLayer.data["EminP"]*6)#self.dataLayer.data["P1"])
            else:
                self.dataLayer.data["P_minuten"] = self.dataLayer.data["P_minuten"][1:]
                self.dataLayer.data["P_minuten"].append(self.dataLayer.data["EminP"]*6)#self.dataLayer.data["P1"])
            
            self.dataLayer.data["P_minuten"][0] = len(self.dataLayer.data["P_minuten"])
            async with self.wattmeterInterface as w:
                await w.writeWattmeterRegister(100,[1])
            self.lastMinute = int(time.localtime()[4]) 
            
        if self.timeInit:
            if self.lastHour is not int(time.localtime()[3]):
                async with self.wattmeterInterface as w:
                    await w.writeWattmeterRegister(101,[1])
                self.lastHour = int(time.localtime()[3])
                if len(self.dataLayer.data["E_hour"])<97:
                    self.dataLayer.data["E_hour"].append(self.lastHour)
                    self.dataLayer.data["E_hour"].append(self.dataLayer.data["EhourP"])
                    self.dataLayer.data["E_hour"].append(self.dataLayer.data["EhourN"])
                    self.dataLayer.data["E_hour"].append(self.dataLayer.data["AC_IN"])
                else:
                    self.dataLayer.data["E_hour"] = self.dataLayer.data["E_hour"][4:]
                    self.dataLayer.data["E_hour"].append(self.lastHour)
                    self.dataLayer.data["E_hour"].append(self.dataLayer.data["EhourP"])
                    self.dataLayer.data["E_hour"].append(self.dataLayer.data["EhourN"])
                    self.dataLayer.data["E_hour"].append(self.dataLayer.data["AC_IN"])
            
                self.dataLayer.data["E_hour"][0] = len(self.dataLayer.data["E_hour"])
            
            else:
                if len(self.dataLayer.data["E_hour"])<97:
                    self.dataLayer.data["E_hour"][len(self.dataLayer.data["E_hour"])-3]= self.dataLayer.data["EhourP"]
                    self.dataLayer.data["E_hour"][len(self.dataLayer.data["E_hour"])-2]= self.dataLayer.data["EhourN"]
                    self.dataLayer.data["E_hour"][len(self.dataLayer.data["E_hour"])-1]=  self.dataLayer.data["AC_IN"]
                else:
                    self.dataLayer.data["E_hour"][94]= self.dataLayer.data["EhourP"]
                    self.dataLayer.data["E_hour"][95]= self.dataLayer.data["EhourN"]
                    self.dataLayer.data["E_hour"][96]=  self.dataLayer.data["AC_IN"]
        
        if (self.lastDay is not int(time.localtime()[2]))and self.timeInit and self.timeOfset:

            day = {("{0:02}/{1:02}/{2}".format(self.lastMounth,self.lastDay ,str(self.lastYear)[-2:] )) : [self.dataLayer.data["E1dP"] + self.dataLayer.data["E2dP"]+self.dataLayer.data["E3dP"], self.dataLayer.data["E1dN"] + self.dataLayer.data["E2dN"]+self.dataLayer.data["E3dN"]]}
            async with self.wattmeterInterface as w:
                await w.writeWattmeterRegister(102,[1])
            self.lastDay = int(time.localtime()[2])
            self.fileHandler.handleData(self.DAILY_CONSUMPTION)
            self.fileHandler.writeData(self.DAILY_CONSUMPTION, day)
            self.dataLayer.data["DailyEnergy"] = self.fileHandler.readData(self.DAILY_CONSUMPTION) 
        
        if (self.lastMounth is not int(time.localtime()[1]))and self.timeInit and self.timeOfset:
            self.lastMounth = int(time.localtime()[1])
        
        if (self.lastYear is not int(time.localtime()[0]))and self.timeInit and self.timeOfset:
            self.lastYear = int(time.localtime()[0])
    
    async def __readWattmeter_data(self,reg,length):
        async with self.wattmeterInterface as w:
                receiveData =  await w.readWattmeterRegister(reg,length)
       
        try:
            if (receiveData != "Null") and (reg == 1000):
                self.dataLayer.data["I1"] =     int(((receiveData[0]) << 8) | (receiveData[1]))
                self.dataLayer.data["I2"] =     int(((receiveData[2]) << 8) | (receiveData[3]))
                self.dataLayer.data["I3"] =     int(((receiveData[4]) << 8) | (receiveData[5]))
                self.dataLayer.data["U1"] =     int(((receiveData[6]) << 8) | (receiveData[7]))
                self.dataLayer.data["U2"] =     int(((receiveData[8]) << 8) | (receiveData[9]))
                self.dataLayer.data["U3"] =     int(((receiveData[10]) << 8) | (receiveData[11]))
                self.dataLayer.data["P1"] =     int(((receiveData[12]) << 8) | (receiveData[13]))
                self.dataLayer.data["P2"] =     int(((receiveData[14]) << 8) | (receiveData[15]))
                self.dataLayer.data["P3"] =     int(((receiveData[16]) << 8) | (receiveData[17]))
                self.dataLayer.data["S1"] =     int(((receiveData[18]) << 8) | (receiveData[19]))
                self.dataLayer.data["S2"] =     int(((receiveData[20]) << 8) | (receiveData[21]))
                self.dataLayer.data["S3"] =     int(((receiveData[22]) << 8) | (receiveData[23]))
     
                return "SUCCESS_READ"
                
            if (receiveData != "Null") and (reg == 200):
                a = (int)(receiveData[0]<< 8)  | receiveData[1]
                if a == 1 and  '1'== __config__.Config().getConfig()['sw,AC IN ACTIVE: HIGH']:
                    self.dataLayer.data["AC_IN"] = 1
                elif a == 0 and  '0'== __config__.Config().getConfig()['sw,AC IN ACTIVE: HIGH']:
                    self.dataLayer.data["AC_IN"] = 1
                else:
                    self.dataLayer.data["AC_IN"] = 0

                return "SUCCESS_READ"
            
            elif (receiveData != "Null") and (reg == 1015):
                self.dataLayer.data["PF1"] = int(((receiveData[0]) << 8) | (receiveData[1]))
                self.dataLayer.data["PF2"] = int(((receiveData[2]) << 8) | (receiveData[3]))
                self.dataLayer.data["PF3"] = int(((receiveData[4]) << 8) | (receiveData[5]))
                return "SUCCESS_READ"
            
            elif (receiveData != "Null") and (reg == 2502):
                self.dataLayer.data["EminP"] = int(((receiveData[0]) << 8) | receiveData[1]) + int(((receiveData[2])<< 8)|receiveData[3]) + int((receiveData[4] << 8) |receiveData[5])
                return "SUCCESS_READ"
             
            elif (receiveData != "Null") and (reg == 2802):
                self.dataLayer.data["EhourP"] = int(((receiveData[0]) << 8) | (receiveData[1])) + int(((receiveData[2]) << 8) | receiveData[3]) + int(((receiveData[4]) << 8) | receiveData[5])
                self.dataLayer.data["EhourN"] = int(((receiveData[6]) << 8) | (receiveData[7])) + int(((receiveData[8]) << 8) | receiveData[9]) + int(((receiveData[10]) << 8) |receiveData[11])
                return "SUCCESS_READ"

            elif (receiveData != "Null") and (reg == 3102):
                
                self.dataLayer.data["E1dP"]= int((receiveData[0] << 8) | receiveData[1])
                self.dataLayer.data["E2dP"]= int((receiveData[2] << 8) | receiveData[3])
                self.dataLayer.data["E3dP"]= int((receiveData[4] << 8) | receiveData[5])
                self.dataLayer.data["E1dN"]= int((receiveData[6] << 8) | receiveData[7])
                self.dataLayer.data["E2dN"]= int((receiveData[8] << 8) | receiveData[9])
                self.dataLayer.data["E3dN"]= int((receiveData[10] << 8) | receiveData[11])
                self.dataLayer.data["PP1p"]= int(((receiveData[12]) << 8) | receiveData[13])
                self.dataLayer.data["PP2p"]= int(((receiveData[14]) << 8) | receiveData[15])
                self.dataLayer.data["PP3p"]= int(((receiveData[16]) << 8) | receiveData[17])
                self.dataLayer.data["PN1p"]= int(((receiveData[18]) << 8) | receiveData[19])
                self.dataLayer.data["PN2p"]= int(((receiveData[20]) << 8) | receiveData[21])
                self.dataLayer.data["PN3p"]= int(((receiveData[22]) << 8) | receiveData[23])
                return "SUCCESS_READ"
                    
            elif (receiveData != "Null") and (reg == 4000):
                
                self.dataLayer.data["E1tP"]= int((receiveData[2] << 24) | (receiveData[3] << 16) | (receiveData[0] << 8) | receiveData[1])
                self.dataLayer.data["E2tP"]= int((receiveData[6] << 24) | (receiveData[7] << 16) | (receiveData[4] << 8) | receiveData[5])
                self.dataLayer.data["E3tP"]= int((receiveData[10] << 24) | (receiveData[11] << 16) | (receiveData[8] << 8) | receiveData[9])
                self.dataLayer.data["E1tN"]= int((receiveData[14] << 24) | (receiveData[15] << 16) | (receiveData[12] << 8) | receiveData[13])
                self.dataLayer.data["E2tN"]= int((receiveData[18] << 24) | (receiveData[19] << 16) | (receiveData[16] << 8) | receiveData[17])
                self.dataLayer.data["E3tN"]= int((receiveData[22] << 24) | (receiveData[23] << 16) | (receiveData[20] << 8) | receiveData[21])

                return "SUCCESS_READ"
            
            elif (receiveData != "Null") and (reg == 2902):
                
                self.dataLayer.data["EpDP"]= int(((receiveData[0]) << 8) | receiveData[1]) + int(((receiveData[2]) << 8) | receiveData[3]) + int(((receiveData[4])<< 8) | receiveData[5])
                self.dataLayer.data["EpDN"]= int(((receiveData[6]) << 8) | receiveData[7]) + int(((receiveData[8]) << 8) | receiveData[9]) + int(((receiveData[10]) << 8) | receiveData[11])
                return "SUCCESS_READ"

            else:   
                return "Timed out waiting for result."
            
        except Exception as e:
            return "Exception: {}. UART is probably not connected.".format(e)
        
    def negotiationRelay(self):
        if self.relay.value():
            self.relay.off()
            self.dataLayer.data["RELAY"]=0
            return False
        else:
            self.relay.on()
            self.dataLayer.data["RELAY"]=1
            return True
        
    def controlRelay(self):
        config = __config__.Config()
        if (config.getConfig()['sw,WHEN OVERFLOW: RELAY ON']) == '1':
            I1_N = 0
            I2_N = 0
            I3_N = 0 
            maxCurrent = 0
            if self.dataLayer.data["I1"] > 32767:
                I1_N = (self.dataLayer.data["I1"] - 65535)/100
            if self.dataLayer.data["I2"] > 32767:
                I2_N = (self.dataLayer.data["I2"] - 65535)/100
            if self.dataLayer.data["I3"] > 32767:
                I3_N = (self.dataLayer.data["I3"] - 65535)/100
            if (I1_N > 0)or(I2_N > 0)or(I3_N > 0):
                self.relay.on()
            else:
                self.relay.off()       
        elif (config.getConfig()['sw,WHEN AC IN: RELAY ON']) == '1':
            if self.dataLayer.data["AC_IN"] == 1:
                self.relay.on()
            else:
                self.relay.off()
        if self.relay.value():
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
        self.data["PF1"] =0#power factor L1
        self.data["PF2"] =0#power factor L2
        self.data["PF3"] =0#power factor L3
        self.data["PP1p"] = 0#positive power peak L1
        self.data["PP2p"] = 0#positive power peak L2
        self.data["PP3p"] = 0#positive power peak L3
        self.data["PN1p"] = 0#negative power peak L1
        self.data["PN2p"] = 0#negative power peak L2
        self.data["PN3p"] = 0#negative power peak L3
        self.data["EminP"] = 0
        self.data["EhourP"] = 0
        self.data["EhourN"] = 0
        self.data["P1"] = 0
        self.data["P2"] = 0
        self.data["P3"] = 0
        self.data["S1"] = 0
        self.data["S2"] = 0
        self.data["S3"] = 0
        self.data["AC_IN"] = 0
        self.data["P_minuten"] = [0]
        self.data["E_hour"] = [0]
        self.data['DailyEnergy'] = None 
        self.data['MounthlyEnergy'] = None 
        self.data["E1dP"] = 0
        self.data["E2dP"] = 0
        self.data["E3dP"] = 0
        self.data["E1dN"] = 0
        self.data["E2dN"] = 0
        self.data["E3dN"] = 0
        self.data["EpDP"] = 0#positive previous day Energy L1,L2,L3
        self.data["EpDN"] = 0#negative previous day Energy L1,L2,L3
        self.data["E1tP"] = 0#positive total Energy L1
        self.data["E2tP"] = 0#positive total Energy L1
        self.data["E3tP"] = 0#positive total Energy L1
        self.data["E1tN"] = 0#negative total Energy L1
        self.data["E2tN"] = 0#negative total Energy L1
        self.data["E3tN"] = 0#negative total Energy L1
        self.data['RUN_TIME'] = 0
        self.data['WATTMETER_TIME'] = 0
        self.data['ID'] = 0
         
class fileHandler:
            
    def handleData(self,file):
        try:
            data = self.readData(file)
        except OSError:
            return
        
        if len(data)>30:
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