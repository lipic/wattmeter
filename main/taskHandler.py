import uasyncio as asyncio
import ledHandler
import time
import wattmeterComInterface
import evseComInterface
from ntptime import settime
from asyn import Lock,NamedTask,Event
from gc import mem_free, collect
from machine import Pin,WDT, RTC
from main import webServerApp
import wifiManager
import semaphore
from main import wattmeter
from main import evse
from main import __config__
import pool
import modbusTcp


EVSE_ERR = 1
WATTMETER_ERR = 2
WEBSERVER_CANCELATION_ERR = 4
WIFI_HANDLER_ERR = 8
TIME_SYNC_ERR = 16

AP = 1
WIFI = 2

class TaskHandler:
    def __init__(self,wifi):
        wattInterface = wattmeterComInterface.Interface(9600,lock = Lock(200))
        evseInterface = evseComInterface.Interface(9600,lock = Lock(200))
        self.wattmeter = wattmeter.Wattmeter(wattInterface) #Create instance of Wattmeter
        self.evse = evse.Evse(self.wattmeter,evseInterface)
        self.webServerApp = webServerApp.WebServerApp(wifi,self.wattmeter, self.evse,wattInterface,evseInterface) #Create instance of Webserver App
        self.uModBusTCP = modbusTcp.Server(wattInterface,evseInterface)
        self.settingAfterNewConnection = False
        self.wdt = WDT(timeout=60000) 
        self.setting = __config__.Config()
        self.wifiManager = wifi
        self.ledErrorHandler = ledHandler.ledHandler(21,1,2,40)
        self.ledWifiHandler =  ledHandler.ledHandler(22,1,2,20) # set pin high on creation
        self.ledRun  = Pin(23, Pin.OUT) # set pin high on creation
        self.errors = 0
        self.tryOfConnections = 0
        self.wifiManager.turnONAp()#povolit Access point
        self.tasksList = {'timeHandler':[self.timeHandler,100],
                                      'localWebserverHandler':[self.localWebserverHandler,20],
                                      'ledErrorHandler':[self.ledErrorHandler.ledHandler,1],
                                      'ledWifiHandler':[self.ledWifiHandler.ledHandler,1],
                                      'wifihandler':[self.wifiHandler,2],
                                      'systemHandler':[self.systemHandler,5]}
     
    def memFree(self):
        before = mem_free()
        collect()
        after = mem_free()
        #print("Memory before: {} & After: {}".format(before,after))
        
    async def routineHandler(self):
        pol = pool.Pool(5)
        counter100ms = 0
        while True:
            for i in self.tasksList:
                if counter100ms% self.tasksList[i][1] == 0:
                    pol.put(self.tasksList[i][0]())
            async for result in pol:
                pass
            counter100ms +=1
            if(counter100ms>1000):
                counter100ms = 1
            await asyncio.sleep(0.1)
            
    async def timeHandler(self):
        if self.wifiManager.isConnected() and self.wattmeter.timeInit == False:
            try:
                print("Setting time")
                settime()
                rtc=RTC()
                import utime
                tampon1=utime.time() 
                tampon2=tampon1+int(self.setting.getConfig()["in,TIME-ZONE"])*3600
                (year, month, mday, hour, minute, second, weekday, yearday)=utime.localtime(tampon2)
                rtc.datetime((year, month, mday, 0, hour, minute, second, 0))
                self.wattmeter.timeInit = True
                self.ledErrorHandler.removeState(TIME_SYNC_ERR)
                self.errors &= ~TIME_SYNC_ERR
            except Exception as e:
                self.ledErrorHandler.addState(TIME_SYNC_ERR)
                self.errors |= TIME_SYNC_ERR
                print("Error during time setting: {}".format(e))        

            self.memFree()
            
  
    async def wifiHandler(self):
        try:
            if(self.wifiManager.isConnected() == True):
                self.ledWifiHandler.addState(WIFI)
                if(self.settingAfterNewConnection == False):
                    self.settingAfterNewConnection = True
                    ip = self.wifiManager.getIp()
                    if((NamedTask.is_running('app2')) == False):
                        loop = asyncio.get_event_loop()
                        loop.create_task(NamedTask('app2',self.webServerApp.webServerRun,1,ip,'app2')())
                    else:
                        print("Webserver is running")
            else:
                self.ledWifiHandler.removeState(WIFI)
                if (len(self.wifiManager.read_profiles())!= 0):
                    try:
                        if(((NamedTask.is_running('app2')) == True)):
                            self.settingAfterNewConnection = False
                            res = await NamedTask.cancel('app2')
                            if res: 
                                print('app2 will be cancelled when next scheduled')
                            else:
                                print('app2 was not cancellable.')                              
                        self.ledErrorHandler.removeState(WEBSERVER_CANCELATION_ERR)
                        self.errors &= ~WEBSERVER_CANCELATION_ERR
                    except Exception as e:
                        self.ledErrorHandler.addState(WEBSERVER_CANCELATION_ERR)
                        self.errors |= WEBSERVER_CANCELATION_ERR
                        print("Error during cancelation: {}".format(e))
                            
                    if(self.tryOfConnections > 30):
                        self.tryOfConnections = 0
                        result = await self.wifiManager.get_connection()
                        if result:
                            self.settingAfterNewConnection = False
                    self.tryOfConnections = self.tryOfConnections + 1
            self.ledErrorHandler.removeState(WIFI_HANDLER_ERR)
            self.errors &= ~WIFI_HANDLER_ERR
        except Exception as e:
            self.ledErrorHandler.addState(WIFI_HANDLER_ERR)
            self.errors |= WIFI_HANDLER_ERR
            print("wifiHandler exception : {}".format(e))
        self.memFree()
            
        
    async def localWebserverHandler(self):
        if((NamedTask.is_running('app1')) == False):
                self.ledWifiHandler.addState(AP)
                loop = asyncio.get_event_loop()
                loop.create_task(NamedTask('app1',self.webServerApp.webServerRun,1,'192.168.4.1','app1')())
        
        if((NamedTask.is_running('app1')) == True):
            self.ledWifiHandler.addState(AP)
        else:
            self.ledWifiHandler.removeState(AP)
        self.memFree()         
            
            
    async def interfaceHandler(self):
        while True:
            try:
                status = await self.evse.evseHandler()
                self.ledErrorHandler.removeState(EVSE_ERR)
                self.errors &= ~EVSE_ERR
            except Exception as e:
                self.ledErrorHandler.addState(EVSE_ERR)
                self.errors |= EVSE_ERR
                print("EVSE error: {}".format(e))
            self.memFree()
            try:
                status = await self.wattmeter.wattmeterHandler()
                self.ledErrorHandler.removeState(WATTMETER_ERR)
                self.errors &= ~WATTMETER_ERR
            except Exception as e:
                self.ledErrorHandler.addState(WATTMETER_ERR)
                self.errors |= WATTMETER_ERR
                print("WATTMETER error: {}".format(e))
            self.memFree()
            await asyncio.sleep(1.5)

    #Handler for time
    async def systemHandler(self):
        self.setting.config['ERROR'] = (str)(self.errors)
        self.wdt.feed()#WDG Handler 
        if(self.ledRun.value()):
            self.ledRun.off()
        else:
            self.ledRun.on()
        self.memFree()
            
    def mainTaskHandlerRun(self):
        #asyncio.core.DEB=1
        asyncio.set_debug(True)
        loop = asyncio.get_event_loop()
        loop.create_task(self.routineHandler())
        loop.create_task(self.interfaceHandler())
        loop.create_task(NamedTask('app1',self.webServerApp.webServerRun,1,'192.168.4.1','app1')())
        loop.create_task(self.uModBusTCP.run(debug=True))
        loop.run_forever()
