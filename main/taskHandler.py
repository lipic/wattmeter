from main import webServerApp
from machine import Pin
from main import wifiManager
import uasyncio as asyncio 
from main import wattmeter
from main import evse
from main import loggingHandler
from main import __config__

class TaskHandler:
    def __init__(self,wifiManager,wlanStatus,logging):
        self.setting = __config__.Config()
        self.setting.update_Config()
        self.log= loggingHandler.LoggingHandler()
        self.wattmeter = wattmeter.Wattmeter(ID=1,timeout=50,baudrate =9600,rxPin=26,txPin=27) #Create instance of Wattmeter
        self.evse = evse.Evse(baudrate = 9600)
        self.webServerApp = webServerApp.WebServerApp(wifiManager,wlanStatus,self.wattmeter,self.log,setting = self.setting, evse = self.evse) #Create instance of Webserver App
        self.wlanStatus = wlanStatus #Get WIFi status from boot process
        self.wifiManager = wifiManager #Get insatnce of wifimanager from boots
        self.ledRun  = Pin(23, Pin.OUT) # set pin high on creation
        self.ledWifi = Pin(22, Pin.OUT) # set pin high on creation
        self.ledErr  = Pin(21, Pin.OUT) # set pin high on creation
        if (logging == True):
            self.log.Logging = True
     
    #Handler for wifi.    
    async def getWifiStatus(self,delay_secs):
        while True:
            try:
                if(self.wlanStatus.isconnected()):
                    self.ledWifi.on()
                else:
                    if len(self.wifiManager.read_profiles()) != 0:
                        self.wifiManager.get_connection()
            except Exception as e:
                self.log.write("Exception: {0}".format(e))
            await asyncio.sleep(10)   

     #Handler for led run.        
    async def ledHandler(self,delay_secs):
        while True:
            if(self.ledRun.value()):
                self.ledRun.off()
            else:
                self.ledRun.on()
            await asyncio.sleep(delay_secs)
            
     #Handler for wattmeter.        
    async def wattmeterHandler(self,delay_secs):
       while True:
          
            status = await self.wattmeter.update_Data(1000,6)
            self.log.write("{} -> {}".format(type(self.wattmeter),status))
            
            status = await self.wattmeter.update_Data(2000,6)
            self.log.write("{} -> {}".format(type(self.wattmeter),status))
            
            status = await self.wattmeter.update_Data(3000,3)
            self.log.write("{} -> {}".format(type(self.wattmeter),status))
            
            await asyncio.sleep(delay_secs)
            
     #Handler for evse.        
    async def evseHandler(self,delay_secs):
       while True:
          
            status = await self.evse.update_Data(1000,3)
            self.log.write("{} -> {}".format(type(self.evse),status))
            
            await asyncio.sleep(delay_secs)

    def mainTaskHandlerRun(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.ledHandler(1))
        loop.create_task(self.getWifiStatus(10))
        loop.create_task(self.wattmeterHandler(1))
        loop.create_task(self.evseHandler(1))
        loop.create_task(self.webServerApp.webServerRun(0))
        loop.run_forever();