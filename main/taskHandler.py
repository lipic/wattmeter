from main import webServerApp
from machine import Pin
from main import wifiManager
import uasyncio as asyncio  
from main import wattmeter
from main import evse
from main import __config__
from main import modbusTcp
from ntptime import settime
import utime
import machine
import gc
                    

class TaskHandler:
    def __init__(self,wifiManager,logging):
        self.wattmeter = wattmeter.Wattmeter(lock = True, ID=1,timeout=50,baudrate =9600,rxPin=26,txPin=27) #Create instance of Wattmeter
        self.evse = evse.Evse(baudrate = 9600, wattmeter = self.wattmeter, lock = True)
        self.webServerApp = webServerApp.WebServerApp(wifiManager,self.wattmeter, evse = self.evse) #Create instance of Webserver App
        self.wifiManager = wifiManager #Get insatnce of wifimanager from boots
        self.ledRun  = Pin(23, Pin.OUT) # set pin high on creation
        self.ledWifi = Pin(22, Pin.OUT) # set pin high on creation
        self.ledErr  = Pin(21, Pin.OUT) # set pin high on creation
        self.rel= Pin(25, Pin.OUT)
        self.uModBusTCP = modbusTcp.Server(self.wattmeter)
        self.settingAfterNewConnection = False
        self.wdt = machine.WDT(timeout=60000)
        self.setting = __config__.Config()

     
     #Handler for time
    async def timeHandler(self,delay_secs):
        while True:
            before = gc.mem_free()
            gc.collect()
            after = gc.mem_free()
            print("Memory beofre: {} & after: {}".format(before,after))
            self.wdt.feed()
            
            await asyncio.sleep(delay_secs)
            
    #Handler for wifi.    
    async def getWifiStatus(self,delay_secs):
        tryOfConnections = 0
        while True:
            try:
                if(self.wifiManager.isConnected() == True):
                    setting = self.setting.getConfig()
                    settime()
                    rtc=machine.RTC()
                    tampon1=utime.time() 
                    tampon2=tampon1+int(setting["sl,TIME-ZONE"])*3600
                    (year, month, mday, hour, minute, second, weekday, yearday)=utime.localtime(tampon2)
                    rtc.datetime((year, month, mday, 0, hour, minute, second, 0))
                    
                    if(self.settingAfterNewConnection == False):
                        self.ledWifi.on()
                        self.settingAfterNewConnection = True
                        loop = asyncio.get_event_loop()
                        ip = self.wifiManager.getIp()
                        loop.run_until_complete(self.webServerApp.webServerRun(0,ip))

                else:
                    if(self.ledWifi.value()):
                        self.ledWifi.off()
                    else:
                        self.ledWifi.on()
                    if (len(self.wifiManager.read_profiles())!= 0) and (self.settingAfterNewConnection == True):
                        if(tryOfConnections > 30):
                            self.settingAfterNewConnection = False
                        await self.wifiManager.get_connection()                    

            except Exception as e:
                print("WIFI: ",e)
   
            gc.collect()
            gc.mem_free()
            await asyncio.sleep(delay_secs)   

     #Handler for led run.        
    async def ledHandler(self,delay_secs):
        while True:
            if(self.ledRun.value()):
                #self.rel.off()
                self.ledRun.off()
            else:
                self.ledRun.on()
                #self.rel.on()
            await asyncio.sleep(delay_secs)
            
     #Handler for wattmeter.        
    async def wattmeterHandler(self,delay_secs):
       while True:
            try:
                status = await self.wattmeter.wattmeterHandler()
            except Exception as e:
                print("Wattmeter error: ",e)
                #self.log.write("{} -> {}".format(type(self.wattmeter),e))
            
            gc.collect()
            gc.mem_free()
            await asyncio.sleep(delay_secs)
            
     #Handler for evse.        
    async def evseHandler(self,delay_secs):
       while True:
            try:
                status = await self.evse.evseHandler()
            except Exception as e:
                print("EVSE error: ",e)
                #self.log.write("{} -> {}".format(type(self.evse),e))
                
            gc.collect()
            gc.mem_free()
            await asyncio.sleep(delay_secs)
            
    async def modbusTcpHandler(self,delay_secs):
        while True:
            await self.uModBusTCP.run()
            await asyncio.sleep(delay_secs)
 
    def mainTaskHandlerRun(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.ledHandler(1))
        loop.create_task(self.getWifiStatus(2))
        loop.create_task(self.evseHandler(1))
        loop.create_task(self.timeHandler(1))
        loop.create_task(self.webServerApp.webServerRun(0,'192.168.4.1'))
        loop.create_task(self.uModBusTCP.run(loop))
        loop.create_task(self.wattmeterHandler(1))
        loop.run_forever()