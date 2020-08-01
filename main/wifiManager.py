import network
import uasyncio as asyncio
import time

class WifiManager:
    
    def __init__(self,ap_ssid, ap_passwd):   
        self.ap_ssid = ap_ssid
        self.ap_password = ap_passwd
        self.ap_authmode = 4  # WPA2
        self.NETWORK_PROFILES = 'wifi.dat'
        self.wlan_ap = network.WLAN(network.AP_IF)
        self.wlan_sta = network.WLAN(network.STA_IF)  
    
    async def get_connection(self):
        connected = False
        try:
            if self.isConnected():
                return self.wlan_sta

            # Read known network profiles from file
            profiles = self.read_profiles()
            # Search WiFis in range 
            self.wlan_sta.active(True)
            networks = self.wlan_sta.scan()

            AUTHMODE = {0: "open", 1: "WEP", 2: "WPA-PSK", 3: "WPA2-PSK", 4: "WPA/WPA2-PSK"}
            for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
                ssid = ssid.decode('utf-8')
                encrypted = authmode > 0
                print("ssid: %s chan: %d rssi: %d authmode: %s" % (ssid, channel, rssi, AUTHMODE.get(authmode, '?')))
                if encrypted:
                    if ssid in profiles:
                        password = profiles[ssid]
                        connected = await self.do_connect(ssid, password)
                else:  # open
                    if ssid in profiles:
                        connected = await self.do_connect(ssid, None)

        except Exception as e:
            print("wifiManager exception: {0}".format(e))

        # start web server for connection manager:
        self.wlan_ap.active(True)
        self.wlan_ap.config(essid=self.ap_ssid, password=self.ap_password, authmode=self.ap_authmode)
        return self.wlan_sta if connected else None


    def read_profiles(self):
        try:
            with open(self.NETWORK_PROFILES) as f:
                lines = f.readlines()
            profiles = {}
            for line in lines:
                ssid, password = line.strip("\n").split(";")
                profiles[ssid] = password
            return profiles
        except Exception as e:
            return {}

    def write_profiles(self,profiles):
        lines = []
        for ssid, password in profiles.items():
            lines.append("%s;%s\n" % (ssid, password))
        with open(self.NETWORK_PROFILES, "w") as f:
            f.write(''.join(lines))
       
    def getSSID(self):
        ssidUsers = {}
        try:
        # Search WiFis in range            
            self.wlan_sta.active(True)
            networks = self.wlan_sta.scan()
            
            AUTHMODE = {0: "open", 1: "WEP", 2: "WPA-PSK", 3: "WPA2-PSK", 4: "WPA/WPA2-PSK"}
            for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
                ssid = ssid.decode('utf-8')
                ssidUsers[ssid]=rssi
                encrypted = authmode > 0
                print("ssid: %s chan: %d rssi: %d authmode: %s" % (ssid, channel, rssi, AUTHMODE.get(authmode, '?')))
        
        except Exception as e:
            print("getSSID exception: {}".format(e))
    
        return ssidUsers
    
    async def do_connect(self,ssid, password):
        self.wlan_sta.active(True)
        if (self.getCurrentConnectSSID() == ssid):
            print("You are currently connected")
            return "connected"
        
        self.wlan_sta.connect(ssid, password)
        print(self.getWlanInfo(self.wlan_sta.status()), end='')
        for retry in range(150):
            connected = self.wlan_sta.isconnected()
            if connected:
                break
            await asyncio.sleep(0.1)
            print('.', end='')
            
        if connected:
            print('\nConnected. Network config: ', self.wlan_sta.ifconfig())
            return True
        else:
            print('\nFailed. Not Connected to: ' + ssid)
            self.wlan_sta.disconnect()
            return False

    def handle_configure(self,ssid, password):
        
        if len(ssid) == 0:
            print("Please choose ssid client first!")
            return 0
        
        if(len(ssid) > 8):
            if(ssid[:9] == "Wattmeter"):
                print("Can not connect to: Wattmeter")
                return 1

        result = await self.do_connect(ssid, password)
        if(result == "connected"):
            print("Currently connected to: {}".format(ssid))
            return 2
        
        if (result == True):
            try:
                profiles = self.read_profiles()
            except OSError:
                profiles = {}
            profiles[ssid] = password
            self.write_profiles(profiles)
            time.sleep(1)
            print("Success connection to: {}".format(ssid))
            return 3
        else:
            print("Error during connection to: {}, maybe bad PASSWORD".format(ssid))
            return 4

    def getIp(self):
        ip= [] 
        try:
            if(self.wlan_sta.isconnected()):
                ip = self.wlan_sta.ifconfig()
                print("IP addres {0}".format(ip[0]))
                return ip[0]
            else:
                return "192.168.4.1"
        except OSError as e:
            print("exception", str(e))
            return "192.168.4.1"
        
    def isConnected(self):
        if self.wlan_sta.isconnected():
            return True
        else:
            return False
        
    def getCurrentConnectSSID(self):
        if(self.isConnected()):
            return self.wlan_sta.config('essid')
        else:
            return "None"
        
    def getWlanInfo(self, resp):
        if(resp == 200):
            return "BEACON_TIMEOUT"
        if(resp == 201):
            return "NO_AP_FOUND"
        if(resp == 202):
            return "WRONG_PASSWORD"
        if(resp == 203):
            return "ASSOC_FAIL"
        if(resp == 204):
            return "HANDSHAKE_TIMEOUT"
        if(resp == 1000):
            return "IDLE"
        if(resp == 1001):
            return "CONNECTING"
        if(resp == 1010):
            return "GOT_IP"
        
        
    def getStart_connection(self):
        connected = False
        try:
            if self.isConnected():
                return self.wlan_sta

            # Read known network profiles from file
            profiles = self.read_profiles()
            # Search WiFis in range 
            self.wlan_sta.active(True)
            networks = self.wlan_sta.scan()

            AUTHMODE = {0: "open", 1: "WEP", 2: "WPA-PSK", 3: "WPA2-PSK", 4: "WPA/WPA2-PSK"}
            for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
                ssid = ssid.decode('utf-8')
                encrypted = authmode > 0
                print("ssid: %s chan: %d rssi: %d authmode: %s" % (ssid, channel, rssi, AUTHMODE.get(authmode, '?')))
                if encrypted:
                    if ssid in profiles:
                        password = profiles[ssid]
                        connected = self.doStart_connect(ssid, password)
                else:  # open
                    if ssid in profiles:
                        connected = self.doStart_connect(ssid, None)

        except Exception as e:
            print("wifiManager exception: {0}".format(e))

        # start web server for connection manager:
        self.wlan_ap.active(True)
        self.wlan_ap.config(essid=self.ap_ssid, password=self.ap_password, authmode=self.ap_authmode)
        return self.wlan_sta if connected else None

    def doStart_connect(self,ssid, password):
        self.wlan_sta.active(True)
        self.wlan_sta.config(dhcp_hostname=self.ap_ssid)
        if (self.getCurrentConnectSSID() == ssid):
            print("You are currently connected")
            return "connected"
        
        self.wlan_sta.connect(ssid, password)
        print(self.getWlanInfo(self.wlan_sta.status()), end='')
        for retry in range(150):
            connected = self.wlan_sta.isconnected()
            if connected:
                break
            time.sleep(0.1)
            print('.', end='')
            
        if connected:
            print('\nConnected. Network config: ', self.wlan_sta.ifconfig())
            return True
        else:
            print('\nFailed. Not Connected to: ' + ssid)
            self.wlan_sta.disconnect()
            return False
        