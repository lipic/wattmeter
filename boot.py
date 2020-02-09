#version 1.0
import ota_updater 
import wifiManager

wifiClient = wifiManager.wifiManager("OlifeEnergy")

 
def download_and_install_update_if_available():
    bootloader = ota_updater.OTAUpdater('https://github.com/lipic/wattmeter',"")
    boardVersion = bootloader.get_version("")
    githubVersion = bootloader.get_latest_version()
    print("Board version is {}".format(boardVersion))
    print("Current version is {}".format(githubVersion))
    
    if(boardVersion == githubVersion):
        print("Software is up to date")
    else:
        print("I will install updates")
        bootloader.download_and_install_update(githubVersion)
 
def run():
    mainApp()
    
def boot():
    wlan = wifiClient.get_connection()
    
    if wlan.isconnected():
        print("Try check for updates")
        download_and_install_update_if_available()
    else:
        print("Can not check updates, because you are not connected to the Internet")
    
    run()

boot()
 
 
