import network
import socket 
import ure
import time
import machine

class WifiManager:
    
    def __init__(self,ap_ssid, ap_passwd):   
        self.ap_ssid = ap_ssid
        self.ap_password = ap_passwd
        self.ap_authmode = 3  # WPA2
        self.NETWORK_PROFILES = 'wifi.dat'
        self.wlan_ap = network.WLAN(network.AP_IF)
        self.wlan_sta = network.WLAN(network.STA_IF)
    
    def get_connection(self):
        """return a working WLAN(STA_IF) instance or None"""

        # First check if there already is any connection:
        if self.wlan_sta.isconnected():
            return self.wlan_sta

        connected = False
  
        try:
            # ESP connecting to WiFi takes time, wait a bit and try again:
            time.sleep(3)
            if self.wlan_sta.isconnected():
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
                        connected = self.do_connect(ssid, password)
                    else:
                        print("skipping unknown encrypted network")
                else:  # open
                    if ssid in profiles:
                        connected = self.do_connect(ssid, None)

        except Exception as e:
            print("Exception: {0}".format(e))

        # start web server for connection manager:
        self.setToAP()

        return self.wlan_sta if connected else None


    def read_profiles(self):
        with open(self.NETWORK_PROFILES) as f:
            lines = f.readlines()
        profiles = {}
        for line in lines:
            ssid, password = line.strip("\n").split(";")
            profiles[ssid] = password
        return profiles


    def write_profiles(self,profiles):
        lines = []
        for ssid, password in profiles.items():
            lines.append("%s;%s\n" % (ssid, password))
        with open(self.NETWORK_PROFILES, "w") as f:
            f.write(''.join(lines))


    def do_connect(self,ssid, password):
        self.wlan_sta.active(True)
        if self.wlan_sta.isconnected():
            return "You are currently connected"
        print('Trying to connect to %s ...' % ssid )
        print("password %s" %password)
        time.sleep(2)
        self.wlan_sta.connect(ssid, password)
        for retry in range(150):
            connected = self.wlan_sta.isconnected()
            if connected:
                break
            time.sleep(0.1)
            print('.', end='')
            
        if connected:
            print('\nConnected. Network config: ', self.wlan_sta.ifconfig())
        else:
            print('\nFailed. Not Connected to: ' + ssid)
        return connected


    def handle_root(self,client):
        self.wlan_sta.active(True)
        ssids = sorted(ssid.decode('utf-8') for ssid, *_ in self.wlan_sta.scan())
    
        while len(ssids):
            ssid = ssids.pop(0)
       


    def handle_configure(self,ssid, password):

        if len(ssid) == 0:
            return False

        if self.do_connect(ssid, password):
            try:
                profiles = self.read_profiles()
            except OSError:
                profiles = {}
            profiles[ssid] = password
            self.write_profiles(profiles)
            time.sleep(5)

            return True
        else:
            return False 


    def setToAP(self):

        self.wlan_ap.active(True)
        self.wlan_ap.config(essid=self.ap_ssid, password=self.ap_password, authmode=self.ap_authmode)
        print(self.wlan_ap.ifconfig())
        print('and access the ESP via your favorite web browser at 192.168.4.1.')


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

        except OSError as e:
            print("exception", str(e))
    
        return ssidUsers

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
        
        