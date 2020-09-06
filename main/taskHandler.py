import uasyncio as asyncio
import wattmeterComInterface
import evseComInterface
from ntptime import settime
from asyn import Lock,NamedTask
from gc import mem_free, collect
from machine import Pin,WDT, RTC
from main import webServerApp
import wifiManager 
from main import wattmeter
from main import evse
from main import __config__ 
from main import modbusTcp
from main import errorHandler

EVSE_ERR = 1
WATTMETER_ERR = 2
WEBSERVER_CANCELATION_ERR = 4
WIFI_HANDLER_ERR = 8
TIME_SYNC_ERR = 16

class TaskHandler:
    def __init__(self,wifi):
        wattInterface = wattmeterComInterface.Interface(9600,lock = Lock())
        evseInterface = evseComInterface.Interface(9600,lock = Lock())
        self.wattmeter = wattmeter.Wattmeter(wattInterface) #Create instance of Wattmeter
        self.evse = evse.Evse(self.wattmeter,evseInterface)
        self.webServerApp = webServerApp.WebServerApp(wifi,self.wattmeter, self.evse) #Create instance of Webserver App
        self.uModBusTCP = modbusTcp.Server(wattInterface,evseInterface)
        self.settingAfterNewConnection = False
        self.wdt = WDT(timeout=60000)
        self.setting = __config__.Config()
        self.wifiManager = wifi
        self.ledErrorHandler = errorHandler.ErrorHandler()
        self.ledRun  = Pin(23, Pin.OUT) # set pin high on creation
        self.ledWifi = Pin(22, Pin.OUT) # set pin high on creation
     
     #Handler for time
    async def timeHandler(self,delay_secs):
        while True:
            if(self.wifiManager.isConnected() == True):
                setting = self.setting.getConfig()
                try:
                    settime()
                    rtc=RTC()
                    import utime
                    tampon1=utime.time() 
                    tampon2=tampon1+int(setting["sl,TIME-ZONE"])*3600
                    (year, month, mday, hour, minute, second, weekday, yearday)=utime.localtime(tampon2)
                    rtc.datetime((year, month, mday, 0, hour, minute, second, 0))
                    self.wattmeter.timeInit = True
                    self.ledErrorHandler.removeError(TIME_SYNC_ERR)
                except Exception as e:
                    self.ledErrorHandler.addError(TIME_SYNC_ERR)
                    print("Error during time setting: {}".format(e))        
            await asyncio.sleep(delay_secs)
            
    #Handler for time
    async def wdgHandler(self,delay_secs):
        while True:
            self.wdt.feed()          
            await asyncio.sleep(delay_secs)
            
    #Handler for memory
    async def memoryHandler(self,delay_secs):
        while True:
            before = mem_free()
            collect()
            after = mem_free()
         #   print("Memory beofre: {} & after: {}".format(before,after))
            await asyncio.sleep(delay_secs)
                    
    #Handler for wifi.    
    async def wifiHandler(self,delay_secs):
        tryOfConnections = 0
        while True:
            try:
                if(self.wifiManager.isConnected() == True):
                    self.ledWifi.on()
                    if(self.settingAfterNewConnection == False):
                        self.settingAfterNewConnection = True
                        ip = self.wifiManager.getIp()
                        if((NamedTask.is_running('app2')) == False):
                            loop = asyncio.get_event_loop()
                            loop.create_task(NamedTask('app2',self.webServerApp.webServerRun,1,ip,'app2')())
                        else:
                            print("Webserver is running")
                else:
                    if(self.ledWifi.value()): 
                        self.ledWifi.off()
                    else:
                        self.ledWifi.on()    
                
                    if (len(self.wifiManager.read_profiles())!= 0):
                        try:
                            if(((NamedTask.is_running('app2')) == True)):
                                self.settingAfterNewConnection = False
                                res = await NamedTask.cancel('app2')
                                if res: 
                                    print('app2 will be cancelled when next scheduled')
                                else:
                                    print('app2 was not cancellable.')                              
                            self.ledErrorHandler.removeError(WEBSERVER_CANCELATION_ERR)
                        except Exception as e:
                            self.ledErrorHandler.addError(WEBSERVER_CANCELATION_ERR)
                            print("Error during cancelation: {}".format(e))
                            
                        if(tryOfConnections > 30):
                            tryOfConnections = 0
                            result = await self.wifiManager.get_connection()
                            if result:
                                self.settingAfterNewConnection = False
                        tryOfConnections = tryOfConnections + 1
                self.ledErrorHandler.removeError(WIFI_HANDLER_ERR)
            except Exception as e:
                self.ledErrorHandler.addError(WIFI_HANDLER_ERR)
                print("wifiHandler exception : {}".format(e))
   
            await asyncio.sleep(delay_secs)   
            
     #Handler for wattmeter.        
    async def wattmeterHandler(self,delay_secs):
       while True:
            await asyncio.sleep(delay_secs)
            try:
                status = await self.wattmeter.wattmeterHandler()
                self.ledErrorHandler.removeError(WATTMETER_ERR)
            except Exception as e:
                self.ledErrorHandler.addError(WATTMETER_ERR)
                #self.log.write("{} -> {}".format(type(self.wattmeter),e))

            
     #Handler for evse.        
    async def evseHandler(self,delay_secs):
       while True:
            try:
                status = await self.evse.evseHandler()
                self.ledErrorHandler.removeError(EVSE_ERR)
            except Exception as e:
                self.ledErrorHandler.addError(EVSE_ERR)
                #self.log.write("{} -> {}".format(type(self.evse),e))

            await asyncio.sleep(delay_secs)
             
    async def ledHandler(self,delay_secs):
        while True:
            if(self.ledRun.value()):
                self.ledRun.off()
            else:
                self.ledRun.on()
            await asyncio.sleep(delay_secs)
            
    def mainTaskHandlerRun(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.wifiHandler(2))
        loop.create_task(self.timeHandler(600))
        loop.create_task(self.memoryHandler(1))
        loop.create_task(self.wdgHandler(1))
        loop.create_task(self.ledHandler(1))
        loop.create_task(self.wifiHandler(2))
        loop.create_task(self.uModBusTCP.run(loop))
        loop.create_task(self.wattmeterHandler(1))
        loop.create_task(self.evseHandler(1))
        loop.create_task(self.ledErrorHandler.ledErrorHandler())
        loop.create_task(NamedTask('app1',self.webServerApp.webServerRun,1,'192.168.4.1','app1')())
        loop.run_forever()
