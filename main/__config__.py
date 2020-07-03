import bootloader

class Config:
    
    def __init__(self):
        #all variables saved in flash
        self.boot = bootloader.Bootloader('https://github.com/lipic/wattmeter',"")
        self.config = {}
        self.config['bt,RESET WATTMETER'] = 0     #Reg 1000
        self.config['sw,AUTOMATIC UPDATE'] = 0 #Reg 1001
        self.config['txt,ACTUAL SW VERSION']=0  #Reg 1002
        self.config['sw,ENABLE CHARGING']=0       #Reg 1003
        self.config['sl,BREAKER']=6                            #Reg 1004
        self.config['sw,ENABLE BALANCING']=0     #Reg 1005
        
        self.SETTING_PROFILES = 'setting.dat'
        self.handle_configure('txt,ACTUAL SW VERSION',self.boot.get_version(""))


    def resetESP(self):
        import machine
        #hard reset
        machine.reset()
        
    # Update self.config from setting.dat and return dict(config)
    def getConfig(self):
        setting = {}
        try:
            setting = self.read_setting()
        except OSError:
            print("Reading config error, create new config")
            setting = {}
            
        if(len(setting) != len(self.config)):
            print("The length of config doesn't fit")
            with open(self.SETTING_PROFILES, 'w') as filetowrite:
                filetowrite.write('')
                filetowrite.close()
                
            for i in self.config: 
                if i in setting:
                    if (self.config[i] != setting[i]):
                        self.config[i] = setting[i]
            setting = {}
             
        for i in self.config: 
            if i in setting:
                if (self.config[i] != setting[i]):
                    self.config[i] = setting[i]
            
            else:
                setting[i] = self.config[i]
                self.write_setting(setting)      
        
        #print("Config: ",self.config)
        return self.config

    # Update self.config. Write new value to self.config and to file setting.dat
    def handle_configure(self,variable, value):
        try:
            if len(variable)>0:
                try:
                    setting = self.read_setting()
                except OSError:
                    setting = {}

                if(variable == "bt,RESET WATTMETER"):
                    if(value == 1):
                        self.resetESP()
                    else:
                        pass
                
                if(setting[variable] != value):
                    setting[variable] = value
                    print(variable,value)
                    self.write_setting(setting)
                    self.getConfig()
                    return True
            else:
                return False
        except Exception as e:
            print(e)
    #If exist read setting from setting.dat, esle create setting
    def read_setting(self):
        with open(self.SETTING_PROFILES) as f:
            lines = f.readlines()
            f.close()
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
            f.close()