#version 1.1
from main import ota_updater 
from main import wifiManager

wifiClient = wifiManager.wifiManager("OlifeEnergy")

 
def download_and_install_update_if_available():
    o = ota_updater.OTAUpdater('https://github.com/lipic/wattmeter', "/main")
    o.download_and_install_update_if_available('wifi-ssid', 'wifi-password')
 
def run():
    mainApp()
    
def boot():
    wlan = wifiClient.get_connection()
    print("tisknu config")
    
    if wlan.isconnected():
        print("Try check for updates")
        download_and_install_update_if_available()
    else:
        print("Can not check updates, because you are not connected to the Internet")

boot()
 
 
