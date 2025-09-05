import bootloader
from collections import OrderedDict
import os
from gc import collect
collect()


class Config: 
    
    def __init__(self):
        self.boot = bootloader.Bootloader('https://github.com/lipic/wattmeter',"")
        self.config = OrderedDict()
        self.config['bt,RESET WATTMETER'] = '0'
        self.config['sw,AUTOMATIC UPDATE'] = '1'
        self.config['txt,ACTUAL SW VERSION'] = '0'
        self.config['sw,ENABLE CHARGING'] = '1'
        self.config['in,MAX-CURRENT-FROM-GRID-A'] = '25'
        self.config['in,TIME-ZONE'] = '2'
        self.config['in,EVSE-NUMBER'] = '1'
        self.config['in,PV-GRID-ASSIST-A'] = '0'
        self.config['in,MAX-P-KW'] = '40'
        self.config['in,MAX-E15-KWH'] = '10'
        self.config['btn,PHOTOVOLTAIC'] = '0'
        self.config['sw,ENABLE BALANCING'] = '1'
        self.config['sw,WHEN AC IN: RELAY ON'] = '0'
        self.config['sw,WHEN OVERFLOW: RELAY ON'] = '0'
        self.config['sw,WHEN AC IN: CHARGING'] = '0'
        self.config['sw,AC IN ACTIVE: HIGH'] = '0'
        self.config['sw,TESTING SOFTWARE'] = '0'
        self.config['sw,Wi-Fi AP'] = '1'          
        self.config['sw,MODBUS-TCP'] = '0'
        self.config['sw,P-E15-GUARD'] = '0'
        self.config['ERRORS'] = '0'
        self.config['ID'] = '0'
        self.config['chargeMode'] = '0'
        self.config['inp,EVSE1'] = '6'
        self.config['inp,EVSE2'] = '6'
        self.config['inp,EVSE3'] = '6'
        self.config['inp,EVSE4'] = '6'
        self.config['inp,EVSE5'] = '6'
        self.config['inp,EVSE6'] = '6'
        self.config['inp,EVSE7'] = '6'
        self.config['inp,EVSE8'] = '6'
        self.config['inp,EVSE9'] = '6'
        self.config['inp,EVSE10'] = '6'
        self.config['DHCP'] = '1'
        self.config['STATIC_IP'] = '192.168.0.130'
        self.config['DNS'] = '100.100.100.100'
        self.config['MASK'] = '255.255.255.0'
        self.config['GATEWAY'] = '192.168.0.1'
        self.config['in,AC-IN-MAX-CURRENT-FROM-GRID-A'] = '25'
        self.SETTING_PROFILES = 'setting.dat'
        self.handle_configure('txt,ACTUAL SW VERSION', self.boot.get_version(""))


    def getConfig(self):
        setting = {}
        try:
            setting = self.read_setting()
        except OSError:
            setting = {}

        if len(setting) != len(self.config):
            with open(self.SETTING_PROFILES, 'w') as filetowrite:
                filetowrite.write('')
                filetowrite.close()
                
            for i in self.config: 
                if i in setting:
                    if self.config[i] != setting[i]:
                        self.config[i] = setting[i]
            setting = {}
        
        for i in self.config: 
            if i in setting:
                if self.config[i] != setting[i]:
                    self.config[i] = setting[i]   
            else:
                setting[i] = self.config[i]
                self.write_setting(setting)
        
        if self.config['ID'] == '0':
            id = bytearray(os.urandom(4))
            randId = ''
            for i in range(0,len(id)):
                randId+= str((int(id[i])))
            self.config['ID'] = randId[-5:]
            self.handle_configure('ID', self.config['ID'])
            
        return self.config

    # Update self.config. Write new value to self.config and to file setting.dat
    def handle_configure(self,variable, value):
        try:
            self.handleDifferentRequests(variable,value)
            if len(variable)>0:
                try:
                    setting = self.read_setting()
                except OSError:
                    setting = {}
                
                if setting[variable] != value:
                    setting[variable] = value
                    self.write_setting(setting)
                    self.getConfig()
                    return True
            else:
                return False
        except Exception as e:
            print(e)
            
    def handleDifferentRequests(self,variable,value):
        if variable == 'bt,RESET WATTMETER':
            from machine import reset
            reset()

    #If exist read setting from setting.dat, esle create setting
    def read_setting(self):
        with open(self.SETTING_PROFILES) as f:
            lines = f.readlines()
        setting = {}
        try:
            for line in lines:
                variable, value = line.strip("\n").split(";")
                setting[variable] = value
            return setting
        
        except Exception as e:
            self.write_setting(self.config)
            return self.config

    # method for write data to file.dat
    def write_setting(self,setting):
        lines = []
        for variable, value in setting.items():
            lines.append("%s;%s\n" % (variable, value))
        with open(self.SETTING_PROFILES, "w") as f:
            f.write(''.join(lines))
            
