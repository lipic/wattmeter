#version 1.0
import bootloader 
from main import wifiManager
from main import main

wifiClient = wifiManager.WifiManager("Wattmeter","123456789")

 
def download_and_install_update_if_available():
    boot = bootloader.OTAUpdater('https://github.com/lipic/wattmeter',"")
    currentVersion = boot.get_version("")
    githubVersion = boot.get_latest_version()
    print("Current version is {}".format(currentVersion))
    print("GitHub version is {}".format(githubVersion))
    
    if(currentVersion == githubVersion):
        print("Software is up to date")
    else:
        print("I will install updates")
        boot.download_and_install_update(githubVersion,currentVersion)
 
    
def boot():
    wlan = wifiClient.get_connection()
    
    if wlan.isconnected():
        print("Try check for updates")
        download_and_install_update_if_available()
    else:
        print("Can not check updates, because you are not connected to the Internet")
    print("Setting main application")
    app = main.mainRoutine(wifiClient)
    print("Starting main application")
    app.run()

boot()
 
 
