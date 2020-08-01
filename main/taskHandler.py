import uasyncio as asyncio  
from ntptime import settime
from asyn import Lock,NamedTask
from gc import mem_free, collect
from machine import Pin, WDT, RTC
from main import webServerApp
from main import wifiManager
from main import wattmeter
from main import evse
from main import __config__
from main import modbusTcp

                    

class TaskHandler:
    def __init__(self,wifiManager,logging):
        self.wattmeter = wattmeter.Wattmeter(lock = Lock(), ID=1,timeout=50,baudrate =9600,rxPin=26,txPin=27) #Create instance of Wattmeter
        self.evse = evse.Evse(baudrate = 9600, wattmeter = self.wattmeter, lock = Lock())
        self.webServerApp = webServerApp.WebServerApp(wifiManager,self.wattmeter, evse = self.evse) #Create instance of Webserver App
        self.wifiManager = wifiManager #Get insatnce of wifimanager from boots
        self.ledRun  = Pin(23, Pin.OUT) # set pin high on creation
        self.ledWifi = Pin(22, Pin.OUT) # set pin high on creation
        self.ledErr  = Pin(21, Pin.OUT) # set pin high on creation
        self.rel= Pin(25, Pin.OUT)
        self.uModBusTCP = modbusTcp.Server(self.wattmeter)
        self.settingAfterNewConnection = False
        self.wdt = WDT(timeout=60000)
        self.setting = __config__.Config()
     
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
                except Exception as e:
                    print(e)          
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
            print("Memory beofre: {} & after: {}".format(before,after))
            await asyncio.sleep(delay_secs)
                    
    #Handler for wifi.    
    async def wifiHandler(self,delay_secs):
        tryOfConnections = 0
        while True:
            try:
                if(self.wifiManager.isConnected() == True):
                    if(self.settingAfterNewConnection == False):
                        self.ledWifi.on()
                        self.settingAfterNewConnection = True
                        ip = self.wifiManager.getIp()
                        if((NamedTask.is_running('app')) == False):
                            loop = asyncio.get_event_loop()
                            loop.create_task(NamedTask('app2',self.webServerApp.webServerRun,0,ip)())
                        else:
                            print("Webserver is running")
                else:
                    if(self.ledWifi.value()): 
                        self.ledWifi.off()
                    else:
                        self.ledWifi.on()
                        
                    if (len(self.wifiManager.read_profiles())!= 0):
                        try:
                            if((NamedTask.is_running('app2')) == True):
                                self.settingAfterNewConnection = False
                                res = await NamedTask.cancel(task_name)
                                if res: 
                                    print(task_name, 'will be cancelled when next scheduled')
                                else:
                                    print(task_name, 'was not cancellable.')                              
                        except Exception as e:
                            print("Error during cancelation: {}".format(e))
                            
                        if(tryOfConnections > 10):
                            tryOfConnections = 0
                            result = await self.wifiManager.get_connection()
                            if result:
                                self.settingAfterNewConnection = False
                        tryOfConnections = tryOfConnections + 1

            except Exception as e:
                print("wifiHandler exception : {}".format(e))
   
            await asyncio.sleep(delay_secs)   

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
            await asyncio.sleep(delay_secs)
            try:
                status = await self.wattmeter.wattmeterHandler()
            except Exception as e:
                print("Wattmeter error: ",e)
                #self.log.write("{} -> {}".format(type(self.wattmeter),e))

            
     #Handler for evse.        
    async def evseHandler(self,delay_secs):
       while True:
            try:
                status = await self.evse.evseHandler()
            except Exception as e:
                print("EVSE error: ",e)
                #self.log.write("{} -> {}".format(type(self.evse),e))

            await asyncio.sleep(delay_secs)
            
    async def modbusTcpHandler(self,delay_secs):
        while True:
            await self.uModBusTCP.run()
            await asyncio.sleep(delay_secs)
 
    def mainTaskHandlerRun(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.timeHandler(600))
        loop.create_task(self.memoryHandler(1))
        loop.create_task(self.ledHandler(1))
        loop.create_task(self.wdgHandler(1))
        loop.create_task(self.wifiHandler(2))
        loop.create_task(self.evseHandler(1))
        loop.create_task(self.uModBusTCP.run(loop))
        loop.create_task(self.wattmeterHandler(1))
        loop.create_task(NamedTask('app1',self.webServerApp.webServerRun,0,'192.168.4.1')())
        loop.run_forever()
