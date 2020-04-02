#version 1.0
import bootloader 
from main import wifiManager
from main import taskHandler
from machine import Pin
import uasyncio as asyncio 
import esp

 # create instance of wificlient and set up AP mode login config
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
  

async def getWifiStatus(self,delay_secs):
    while True:
        if(Pin(21, Pin.OUT).value()):
            Pin(21, Pin.OUT).off()
        else:
            Pin(21, Pin.OUT).on()
        await asyncio.sleep(delay_secs)
        
def boot():
    
    Pin(23, Pin.OUT).off() # set pin high on creation
    Pin(22, Pin.OUT).off() # set pin high on creation
    Pin(21, Pin.OUT).on()  # set pin high on creation
    
    loop = asyncio.get_event_loop()
    loop.create_task(getWifiStatus(0.5))
    loop.run_forever();
    
    # get status of current connection 
    wlan = wifiClient.get_connection()
    try:
        if wlan.isconnected():
            print("Try check for updates")
            download_and_install_update_if_available()
        else:
            print("Can not check updates, because you are not connected to the Internet")
    
    except Exception as e:
        print("Error {0}".format(e))
    print("Setting main application")
    handler = taskHandler.TaskHandler(wifiClient,wlan)
    print("Starting main application")
    
    asyncio.cancel(loop)
    Pin(21, Pin.OUT).off() # set pin high on creation
    handler.mainTaskHandlerRun()

if __name__ == "__main__":
    boot()
 
 
