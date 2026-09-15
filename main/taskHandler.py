import uasyncio as asyncio
import network
import time
import ledHandler
import wattmeterComInterface
import evseComInterface
import ntptime
from asyn import Lock
from gc import mem_free, collect
from machine import Pin, WDT, RTC, reset
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
AP_GRACE_PERIOD_S = 1200

WEB_WDT_STARTUP_S = 300
WEB_WDT_PERIOD_S = 60
WEB_WDT_TIMEOUT_S = 20
WEB_WDT_FAIL_LIMIT = 8
WEB_WDT_MAX_LAG_MS = 2000
EV_CHARGING = 3

_ASYNCIO_V3 = hasattr(asyncio, "Loop") and hasattr(asyncio, "wait_for") \
    and hasattr(asyncio, "open_connection")


def _reset_cause():
    # Rozlisi, jestli restart udelal hardwarovy watchdog (zaseknuta smycka),
    # softwarove reset() z kodu, nebo vypadek napajeni.
    try:
        import machine
        cause = machine.reset_cause()
    except Exception:
        return "?"
    for name in ("PWRON_RESET", "HARD_RESET", "WDT_RESET", "DEEPSLEEP_RESET", "SOFT_RESET"):
        if getattr(machine, name, None) == cause:
            return "{} ({})".format(cause, name)
    return str(cause)

_LOG_AP = "AP:"
_LOG_SYS = "sys:"
_LOG_ERR = "err:"
_LOG_WEB = "web:"


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
        self.modbus_tcp = None
        if self.setting.get_switch('sw,MODBUS-TCP', False):
            try:
                from main.modbus_tcp import ModbusTCPServer
                self.modbus_tcp = ModbusTCPServer(wattmeter_data=self.wattmeter.data_layer.data, setting_data=self.setting.config, wifi=wifi, port=502)
            except Exception as e:
                print(_LOG_ERR, 'modbus', e)
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
        self.wlan_ap = network.WLAN(network.AP_IF)
        self.apGrace = AP_GRACE_PERIOD_S
        self.apFailCount = 0
        self.apRequested = None
        self.turnApOn()

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
            print("net:", current_config)
        except Exception as e:
            print(_LOG_ERR, 'ip', e)

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
                    print(_LOG_ERR, 'time', e)

            await asyncio.sleep(10)
            collect()

    def store_dhcp_ifconfig(self):
        ifconfig = self.wifiManager.wlan_sta.ifconfig()
        for index, name in ((0, 'STATIC_IP'), (1, 'MASK'), (2, 'GATEWAY'), (3, 'DNS')):
            if self.setting.config.get(name) != ifconfig[index]:
                self.setting.handle_configure(name, ifconfig[index])

    def isApActive(self):
        try:
            return bool(self.wlan_ap.active())
        except Exception as e:
            print(_LOG_ERR, 'ap', e)
            return None

    def turnApOn(self):
        try:
            self.wlan_ap.active(True)
        except Exception as e:
            print(_LOG_ERR, 'ap', e)
            return
        try:
            self.wlan_ap.config(essid=self.wifiManager.ap_ssid,
                                password=self.wifiManager.ap_password,
                                authmode=self.wifiManager.ap_authmode)
        except Exception as e:
            print(_LOG_ERR, 'ap', e)

    def turnApOff(self):
        try:
            self.wlan_ap.active(False)
        except Exception as e:
            print(_LOG_ERR, 'ap', e)

    def setApState(self, enabled):
        if enabled:
            self.ledWifiHandler.addState(AP)
        else:
            self.ledWifiHandler.removeState(AP)

        current = self.isApActive()
        if current == enabled:
            self.apRequested = enabled
            self.apFailCount = 0
            return
        if current is None and self.apRequested == enabled:
            return

        if enabled:
            self.turnApOn()
        else:
            self.turnApOff()

        current = self.isApActive()
        if current is None:
            self.apRequested = enabled
            self.apFailCount = 0
            print(_LOG_AP, enabled, '?')
        elif current == enabled:
            self.apRequested = enabled
            self.apFailCount = 0
            print(_LOG_AP, enabled)
        else:
            self.apFailCount += 1
            if self.apFailCount == 1 or (self.apFailCount % 60) == 0:
                print(_LOG_AP, enabled, 'x', self.apFailCount)

    async def apHandler(self):
        while True:
            try:
                if self.apGrace > 0:
                    self.apGrace -= 1
                ap_enabled = self.setting.get_switch('sw,Wi-Fi AP', True)
                self.setApState(ap_enabled or self.apGrace > 0)
            except Exception as e:
                print(_LOG_ERR, 'ap', e)
            await asyncio.sleep(1)

    def webProbeIp(self):
        if self.wifiManager.isConnected():
            try:
                return self.wifiManager.wlan_sta.ifconfig()[0]
            except Exception as e:
                print(_LOG_ERR, 'web', e)
                return None
        if self.isApActive():
            return '192.168.4.1'
        return None

    def isCharging(self):
        try:
            for state in self.evse.data_layer.data["EV_STATE"]:
                if state == EV_CHARGING:
                    return True
        except Exception as e:
            print(_LOG_ERR, 'web', e)
        return False

    async def loopIsResponsive(self):
        start = time.ticks_ms()
        await asyncio.sleep_ms(200)
        return time.ticks_diff(time.ticks_ms(), start) - 200 < WEB_WDT_MAX_LAG_MS

    async def webProbe(self):
        ip = self.webProbeIp()
        if ip is None:
            return None
        writer = None
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, self.webServerApp.port), WEB_WDT_TIMEOUT_S)
            writer.write(b"GET /getEspID HTTP/1.0\r\n\r\n")
            await asyncio.wait_for(writer.drain(), WEB_WDT_TIMEOUT_S)
            response = await asyncio.wait_for(reader.read(15), WEB_WDT_TIMEOUT_S)
            ok = response is not None and response.startswith(b"HTTP/")
            # Odpoved je nutne docist az do konce. Kdyz se spojeni zavre driv,
            # server dopisuje do zavreneho socketu a spadne na ECONNRESET,
            # a to pri kazde sonde.
            drained = 0
            while drained < 1024:
                rest = await asyncio.wait_for(reader.read(128), WEB_WDT_TIMEOUT_S)
                if not rest:
                    break
                drained += len(rest)
            return ok
        except Exception as e:
            print(_LOG_WEB, 'err', e)
            return False
        finally:
            if writer is not None:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

    async def webWatchdog(self):
        if not _ASYNCIO_V3:
            print(_LOG_WEB, 'off')
            return

        fails = 0
        proven = False
        await asyncio.sleep(WEB_WDT_STARTUP_S)
        while True:
            try:
                ok = await self.webProbe()
                if ok is None:
                    pass
                elif ok:
                    fails = 0
                    proven = True
                elif not await self.loopIsResponsive():
                    fails = fails - 1 if fails > 0 else 0
                    print(_LOG_WEB, 'busy')
                else:
                    fails += 1
                    print(_LOG_WEB, 'fail', fails)
                    if fails >= WEB_WDT_FAIL_LIMIT:
                        fails = WEB_WDT_FAIL_LIMIT
                        if not proven:
                            print(_LOG_WEB, 'unproven')
                        elif self.isCharging():
                            print(_LOG_WEB, 'charging')
                        else:
                            print(_LOG_WEB, 'reset')
                            await asyncio.sleep(1)
                            reset()
            except Exception as e:
                print(_LOG_ERR, 'web', e)
            await asyncio.sleep(WEB_WDT_PERIOD_S)

    async def wifiHandler(self):
        while True:
            try:
                if self.wifiManager.isConnected():
                    if self.setting.config['DHCP'] == '0' and not self.static_ip_is_set:
                        print("net: static ip")
                        self.set_static_ip()
                    elif self.setting.config['DHCP'] == '1':
                        self.store_dhcp_ifconfig()
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
                print(_LOG_ERR, 'wifi', e)
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
                print(_LOG_ERR, 'watt', e)
            try:
                await self.evse.evse_handler()
                self.ledErrorHandler.removeState(EVSE_ERR)
                self.errors &= ~EVSE_ERR
            except Exception as e:
                self.ledErrorHandler.addState(EVSE_ERR)
                self.errors |= EVSE_ERR
                print(_LOG_ERR, 'evse', e)

            collect()
            await asyncio.sleep(1.5)

    async def system_handler(self):
        # Tenhle task jako jediny krmi hardwarovy watchdog. Kdyby umrel na
        # vyjimce, ostatni tasky bezi dal a deska se za 60 s tvrde restartuje
        # bez jakekoli hlasky - proto je zbytek smycky odstineny.
        tick = 0
        last_err = None
        while True:
            self.wdt.feed()
            try:
                self.setting.config['ERRORS'] = str(self.errors)
                collect()
                tick += 1
                if tick >= 60:  # stav pameti jednou za minutu, kvuli hledani pricin restartu
                    tick = 0
                    print(_LOG_SYS, 'heap', mem_free())
            except Exception as e:
                msg = str(e)
                if msg != last_err:  # stejnou chybu nehlasit kazdou sekundu
                    last_err = msg
                    print(_LOG_ERR, 'sys', msg)
            await asyncio.sleep(1)

    def mainTaskHandlerRun(self):
        print(_LOG_SYS, 'boot reset_cause={} heap={}'.format(_reset_cause(), mem_free()))
        loop = asyncio.get_event_loop()
        loop.create_task(self.wifiHandler())
        loop.create_task(self.apHandler())
        loop.create_task(self.system_handler())
        loop.create_task(self.timeHandler())
        loop.create_task(self.interface_handler())
        loop.create_task(self.ledError())
        loop.create_task(self.ledWifi())
        loop.create_task(self.webServerApp.webServer_run())
        loop.create_task(self.webWatchdog())
        if self.modbus_tcp is not None:
            loop.create_task(self.modbus_tcp.run())
        loop.run_forever()
