import wifiManager
global wlan

try:
    wlan = wifiManager.get_connection()
except:
    print("Could not initialize the network connection.")


 
