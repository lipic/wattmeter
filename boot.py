#version 1.0

import wifiManager
from machine import Pin,freq
from main import __config__

def download_and_install_update_if_available(tst):
    import bootloader
    boot = None
    currentVersion = ''
    if(tst==0):
        boot = bootloader.Bootloader('https://github.com/lipic/wattmeter',"")
    else:
        boot = bootloader.Bootloader('https://github.com/lipic/wattmeter_tst',"",tst=True)
        
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
    
    Pin(23, Pin.OUT).off() # set pin high on creation
    Pin(22, Pin.OUT).off() # set pin high on creation
    Pin(21, Pin.OUT).on()  # set pin high on creation

    config = __config__.Config()
    config = config.getConfig()
    wifiClient = wifiManager.WifiManager("Wattmeter-{}".format(config['ID']),"watt{}".format(config['ID']))
    # get status of current connection 
    wlan = wifiClient.getStart_connection()
    try:
        if wlan.isconnected():
            Pin(23, Pin.OUT).on() # set pin high on creation
            Pin(22, Pin.OUT).on() # set pin high on creation
            if(config['sw,AUTOMATIC UPDATE'] == '1'):
                print("Try check for updates")
                download_and_install_update_if_available(int(config['sw,TESTING SOFTWARE']))
            Pin(23, Pin.OUT).off() # set pin high on creation
            Pin(22, Pin.OUT).off() # set pin high on creation
        else:
            print("Can not check updates, because you are not connected to the Internet")
    
    except Exception as e:
        print("Error {0}".format(e))
    from main import taskHandler
    handler = taskHandler.TaskHandler(wifiClient)
    print("Starting main application")
    Pin(21, Pin.OUT).off() # set pin high on creation
    handler.mainTaskHandlerRun()

if __name__ == "__main__":
    freq(240000000)
    print("Machine freq: {} Mhz".format(freq()/1000000))
    boot()
 
 
