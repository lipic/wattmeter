from main import webServerApp
from machine import Pin
from main import wifiManager
import uasyncio as asyncio 
from main import wattmeter
from main import loggingHandler

class TaskHandler:
    def __init__(self,wifiManager,wlanStatus,logging):
        self.log= loggingHandler.LoggingHandler()
        if (logging == True):
            self.log.enableLogging = True
        self.wattmeter = wattmeter.Wattmeter(ID=1,timeout=50,baudrate =115200,rxPin=26,txPin=27) #Create instance of Wattmeter
        self.webServerApp = webServerApp.WebServerApp(wifiManager,wlanStatus,self.wattmeter,self.log) #Create instance of Webserver App
        self.wlanStatus = wlanStatus #Get WIFi status from boot process
        self.wifiManager = wifiManager #Get insatnce of wifimanager from boots
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
                self.log.write("Exception: {0}".format(e))
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

            await self.wattmeter.readRegs(1000,6)
            status = self.wattmeter.updateData()
            #print(status)
            if status != None:
                self.log.write(status)
            await asyncio.sleep(delay_secs)
            

    def mainTaskHandlerRun(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.ledHandler(1))
        loop.create_task(self.getWifiStatus(10))
        loop.create_task(self.wattmeterHandler(1))
        loop.create_task(self.webServerApp.webServerRun(0))
        loop.run_forever();