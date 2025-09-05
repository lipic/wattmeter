import uasyncio as asyncio
import ledHandler
import wattmeterComInterface
import evseComInterface
import ntptime
from asyn import Lock
from gc import mem_free, collect
from machine import Pin, WDT, RTC
from main import webServerApp
from main import wattmeter
from main import evse
from main import __config__
collect()

EVSE_ERR = 1
WATTMETER_ERR = 2
WEBSERVER_CANCELATION_ERR = 4
WIFI_HANDLER_ERR = 8
TIME_SYNC_ERR = 16

AP = 1
WIFI = 2


class TaskHandler:
    def __init__(self, wifi):
        self.setting = __config__.Config()
        self.setting.getConfig()
        self.wifiManager = wifi
        self.static_ip_is_set = False
        if self.setting.config['DHCP'] == '0':
            if self.wifiManager.isConnected():
                self.set_static_ip()
        wattInterface = wattmeterComInterface.Interface(9600, lock=Lock(200))
        evseInterface = evseComInterface.Interface(9600, lock=Lock(200))
        self.wattmeter = wattmeter.Wattmeter(wattInterface, self.setting)  # Create instance of Wattmeter
        self.evse = evse.Evse(self.wattmeter, evseInterface, self.setting)
        self.webServerApp = webServerApp.WebServerApp(wifi, self.wattmeter, self.evse, wattInterface, evseInterface, self.setting)  # Create instance of Webserver App
        try:
            from main.modbus_tcp import ModbusTCPServer
            self.modbus_tcp = ModbusTCPServer(wattmeter_data=self.wattmeter.data_layer.data, setting_data=self.setting.config, wifi=wifi, port=502)
        except Exception as e:
            import modbusTcp
            self.modbus_tcp = modbusTcp.Server(wattInterface, evseInterface)
        collect()
        self.settingAfterNewConnection = False
        self.wdt = WDT(timeout=60000)
        self.ledErrorHandler = ledHandler.ledHandler(21, 1, 2, 40)
        self.ledWifiHandler = ledHandler.ledHandler(22, 1, 2, 20)
        self.ledRun = Pin(23, Pin.OUT)
        self.errors = 0
        self.tryOfConnections = 0
        self.wifiManager.turnONAp()
        self.apTimeout = 600

    def set_static_ip(self) -> None:
        try:
            ssid = self.wifiManager.wlan_sta.config('essid')
            pwd = ""
            profiles = self.wifiManager.read_profiles()
            if ssid in profiles:
                pwd = profiles[ssid]
            self.wifiManager.disconnect()
            self.wifiManager.wlan_sta.ifconfig((self.setting.config['STATIC_IP'], self.setting.config['MASK'], self.setting.config['GATEWAY'], self.setting.config['DNS']))
            self.wifiManager.wlan_sta.connect(ssid, pwd)
            self.static_ip_is_set = True
            current_config = self.wifiManager.wlan_sta.ifconfig()
            print("Current Network Configuration")
            print("-----------------------------")
            print("IP Address   : {}".format(current_config[0]))
            print("Subnet Mask  : {}".format(current_config[1]))
            print("Gateway      : {}".format(current_config[2]))
            print("DNS Server   : {}".format(current_config[3]))
            print("-----------------------------")
        except Exception as e:
            print(e)

    async def ledWifi(self):
        while True:
            await self.ledWifiHandler.ledHandler()
            await asyncio.sleep(0.1)

    async def ledError(self):
        while True:
            await self.ledErrorHandler.ledHandler()
            await asyncio.sleep(0.1)

    async def timeHandler(self):
        while True:
            if self.wifiManager.isConnected() and self.wattmeter.time_init == False:
                try:
                    print("Setting time")
                    ntptime.host = "129.6.15.28"
                    ntptime.settime()
                    rtc = RTC()
                    import utime
                    tampon1 = utime.time()
                    timezone_offset = int(self.setting.config["in,TIME-ZONE"])
                    tampon2 = tampon1 + timezone_offset * 3600
                    local_time = utime.localtime(tampon2)
                    if len(local_time) == 8:
                        (year, month, mday, hour, minute, second, weekday, yearday) = local_time
                        rtc.datetime((year, month, mday, 0, hour, minute, second, 0))
                        self.wattmeter.time_init = True
                        self.ledErrorHandler.removeState(TIME_SYNC_ERR)
                        self.errors &= ~TIME_SYNC_ERR
                    else:
                        print("Invalid localtime tuple length")

                except Exception as e:
                    self.ledErrorHandler.addState(TIME_SYNC_ERR)
                    self.errors |= TIME_SYNC_ERR
                    print("Error during time setting: {}".format(e))

            await asyncio.sleep(10)
            collect()

    async def wifiHandler(self):
        while True:
            try:
                self.ledWifiHandler.addState(AP)
                if self.wifiManager.isConnected():
                    if self.setting.config['DHCP'] == '0' and not self.static_ip_is_set:
                        print("Re-applying static IP on reconnect")
                        self.set_static_ip()
                    elif self.setting.config['DHCP'] == '1':
                        self.setting.handle_configure('STATIC_IP', self.wifiManager.wlan_sta.ifconfig()[0])
                        self.setting.handle_configure('MASK', self.wifiManager.wlan_sta.ifconfig()[1])
                        self.setting.handle_configure('GATEWAY', self.wifiManager.wlan_sta.ifconfig()[2])
                        self.setting.handle_configure('DNS', self.wifiManager.wlan_sta.ifconfig()[3])

                    if self.apTimeout > 0:
                        self.apTimeout -= 1
                    elif (int(self.setting.config['sw,Wi-Fi AP']) == 0) and self.apTimeout == 0:
                        self.wifiManager.turnOfAp()
                        self.ledWifiHandler.removeState(AP)
                    elif int(self.setting.config['sw,Wi-Fi AP']) == 1:
                        self.wifiManager.turnONAp()
                    self.ledWifiHandler.addState(WIFI)
                    if not self.settingAfterNewConnection:
                        self.settingAfterNewConnection = True
                else:
                    self.static_ip_is_set = False
                    self.ledWifiHandler.removeState(WIFI)
                    if len(self.wifiManager.read_profiles()) != 0:
                        if self.tryOfConnections > 30:
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
            collect()
            await asyncio.sleep(2)

    async def interface_handler(self):
        while True:
            try:
                await self.wattmeter.wattmeter_handler()
                self.ledErrorHandler.removeState(WATTMETER_ERR)
                self.errors &= ~WATTMETER_ERR
            except Exception as e:
                self.ledErrorHandler.addState(WATTMETER_ERR)
                self.errors |= WATTMETER_ERR
                print("WATTMETER error: {}".format(e))
            try:
                await self.evse.evse_handler()
                self.ledErrorHandler.removeState(EVSE_ERR)
                self.errors &= ~EVSE_ERR
            except Exception as e:
                self.ledErrorHandler.addState(EVSE_ERR)
                self.errors |= EVSE_ERR
                print("EVSE error: {}".format(e))

            collect()
            await asyncio.sleep(1.5)

    async def system_handler(self):
        while True:
            self.setting.config['ERRORS'] = (str)(self.errors)
            self.wdt.feed()
            collect()
            await asyncio.sleep(1)

    def mainTaskHandlerRun(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.wifiHandler())
        loop.create_task(self.system_handler())
        loop.create_task(self.timeHandler())
        loop.create_task(self.interface_handler())
        loop.create_task(self.ledError())
        loop.create_task(self.ledWifi())
        loop.create_task(self.webServerApp.webServer_run())
        if self.setting.config['sw,MODBUS-TCP'] == '1':
            loop.create_task(self.modbus_tcp.run())
        loop.run_forever()
