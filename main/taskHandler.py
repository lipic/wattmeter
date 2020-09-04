import uasyncio as asyncio
import wattmeterComInterface
import evseComInterface
from ntptime import settime
from asyn import Lock,NamedTask
from gc import mem_free, collect
from machine import WDT, RTC
from main import webServerApp
import wifiManager 
from main import wattmeter
from main import evse
from main import __config__ 
from main import modbusTcp
from main import gpioHandler

                    

class TaskHandler:
    def __init__(self,wifi):
        wattInterface = wattmeterComInterface.Interface(9600,lock = Lock())
        evseInterface = evseComInterface.Interface(9600,lock = Lock())
        self.wattmeter = wattmeter.Wattmeter(wattInterface) #Create instance of Wattmeter
        self.evse = evse.Evse(self.wattmeter,evseInterface)
        self.webServerApp = webServerApp.WebServerApp(wifi,self.wattmeter, self.evse) #Create instance of Webserver App
        self.ledAPI = gpioHandler.GpioHandler({'LED_RUN':{'config':{'pin':23},'action':{'Ontime':10,'Offtime':20,'timeCnt':0,'Delta':0,'DeltaCnt':0,'repeat':0,'repeatCnt':0}},
                                                                                   'LED_ERR':{'config':{'pin':21},'action':{'Ontime':0,'Offtime':0,'timeCnt':0,'Delta':0,'DeltaCnt':0,'repeat':0,'repeatCnt':0}},
                                                                                   'LED_WIFI':{'config':{'pin':22},'action':{'Ontime':0,'Offtime':0,'timeCnt':0,'Delta':0,'DeltaCnt':0,'repeat':0,'repeatCnt':0}}})
        self.wifiManager = wifi #Get insatnce of wifimanager from boots
        self.uModBusTCP = modbusTcp.Server(wattInterface,evseInterface)
        self.settingAfterNewConnection = False
        self.wdt = WDT(timeout=60000)
        self.setting = __config__.Config()
        self.Webcnt = 1
     
     #Handler for time
    async def timeHandler(self,delay_secs):
        asyncio.set_debug(1)
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
                        self.ledAPI.callback(task='LED_WIFI',type='action',process='Ontime',value=10)
                        self.settingAfterNewConnection = True
                        ip = self.wifiManager.getIp()
                        if((NamedTask.is_running('app2')) == False):
                            loop = asyncio.get_event_loop()
                            loop.create_task(NamedTask('app2',self.webServerApp.webServerRun,1,ip,'app2')())
                        else:
                            print("Webserver is running")
                else:
                    self.ledAPI.callback(task='LED_WIFI',type='action',process='Ontime',value=5)
                    self.ledAPI.callback(task='LED_WIFI',type='action',process='Offtime',value=10)
                        
                    if (len(self.wifiManager.read_profiles())!= 0):
                        try:
                            if(((NamedTask.is_running('app2')) == True)):
                                self.settingAfterNewConnection = False
                                res = await NamedTask.cancel('app2')
                                if res: 
                                    print('app2 will be cancelled when next scheduled')
                                else:
                                    print('app2 was not cancellable.')                              
                        except Exception as e:
                            print("Error during cancelation: {}".format(e))
                            
                        if(tryOfConnections > 30):
                            tryOfConnections = 0
                            result = await self.wifiManager.get_connection()
                            if result:
                                self.settingAfterNewConnection = False
                        tryOfConnections = tryOfConnections + 1

            except Exception as e:
                print("wifiHandler exception : {}".format(e))
   
            await asyncio.sleep(delay_secs)   
            
     #Handler for wattmeter.        
    async def wattmeterHandler(self,delay_secs):
       while True:
            await asyncio.sleep(delay_secs)
            try:
                status = await self.wattmeter.wattmeterHandler()
                if(self.ledAPI.getStatus(task='LED_ERR',type='action',process='repeat')==2):
                    self.ledAPI.callback(task='LED_ERR',type='action',process='Ontime',value=0)
                    self.ledAPI.callback(task='LED_ERR',type='action',process='Offtime',value=0)
            except Exception as e:
                self.ledAPI.callback(task='LED_ERR',type='action',process='Ontime',value=2)
                self.ledAPI.callback(task='LED_ERR',type='action',process='Offtime',value=4)
                self.ledAPI.callback(task='LED_ERR',type='action',process='repeat',value=2)
                self.ledAPI.callback(task='LED_ERR',type='action',process='Delta',value=30)
                #self.log.write("{} -> {}".format(type(self.wattmeter),e))

            
     #Handler for evse.        
    async def evseHandler(self,delay_secs):
       while True:
            try:
                status = await self.evse.evseHandler()
                if(self.ledAPI.getStatus(task='LED_ERR',type='action',process='repeat')==0):
                    self.ledAPI.callback(task='LED_ERR',type='action',process='Ontime',value=0)
                    self.ledAPI.callback(task='LED_ERR',type='action',process='Offtime',value=0)
            except Exception as e:
                self.ledAPI.callback(task='LED_ERR',type='action',process='Ontime',value=2)
                self.ledAPI.callback(task='LED_ERR',type='action',process='Offtime',value=4)
                self.ledAPI.callback(task='LED_ERR',type='action',process='repeat',value=0)
                self.ledAPI.callback(task='LED_ERR',type='action',process='Delta',value=30)
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
        loop.create_task(self.wdgHandler(1))
        loop.create_task(self.wifiHandler(2))
        loop.create_task(self.uModBusTCP.run(loop))
        loop.create_task(self.wattmeterHandler(1))
        loop.create_task(self.evseHandler(1))
        loop.create_task(self.ledAPI.ledHandlerObj())
        loop.create_task(NamedTask('app1',self.webServerApp.webServerRun,1,'192.168.4.1','app1')())
        loop.run_forever()
