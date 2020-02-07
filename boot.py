#version 1.0
import ota_updater 
import wifiManager

global wlan

 
def download_and_install_update_if_available():
    o = ota_updater.OTAUpdater('https://github.com/lipic/wattmeter.git')
    o.download_and_install_update_if_available('wifi-ssid', 'wifi-password')

def boot():
    wlan = wifiManager.get_connection()
    if wlan.isconnected():
        print("Try check for updates")
        download_and_install_update_if_available()
    else:
        print("Can not check updates, because you are not connected to the Internet")

boot()
 
 
