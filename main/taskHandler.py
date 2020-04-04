from main import webServerApp
from machine import Pin
from main import wifiManager
import uasyncio as asyncio 
from main import wattmeter

class TaskHandler:
    def __init__(self,wlan,wlanStatus,logging):
        if (logging == True):
            import  uos
            from main import loggingHandler
            self.logging= loggingHandler.LoggingHandler()
            uos.dupterm(self.logging)
        self.wattmeter = wattmeter.Wattmeter()
        self.webServerApp = webServerApp.WebServerApp(wlan,wlanStatus,self.wattmeter,self.logging)
        self.wlanStatus = wlanStatus
        self.wifiManager = wlan
        self.ledRun  = Pin(23, Pin.OUT) # set pin high on creation
        self.ledWifi = Pin(22, Pin.OUT) # set pin high on creation
        self.ledErr  = Pin(21, Pin.OUT) # set pin high on creation
        
     
        
    async def getWifiStatus(self,delay_secs):
        while True:
            try:
                if(self.wlanStatus.isconnected()):
                    self.ledWifi.on()
                else:
                    if len(self.wifiManager.read_profiles()) != 0:
                        self.wifiManager.get_connection()
            except Exception as e:
                print("Error {0}".format(e))
            await asyncio.sleep(10)   

    async def ledHandler(self,delay_secs):

        while True:
            if(self.ledRun.value()):
                self.ledRun.off()
            else:
                self.ledRun.on()
            await asyncio.sleep(delay_secs)
            
    async def wattmeterHandler(self,delay_secs):
        while True:
            self.wattmeter.updateData
            print("Data {}".format(self.wattmeter.datalayer.data))
            await asyncio.sleep(delay_secs)
            

    def mainTaskHandlerRun(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.ledHandler(1))
        loop.create_task(self.getWifiStatus(10))
        loop.create_task(self.wattmeterHandler(1))
        loop.create_task(self.webServerApp.webServerRun(0))
        loop.run_forever();