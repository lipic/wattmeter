import time
class Config:
    
    def __init__(self):
        #all variables
        self.config = {'sw,Enable balancing':False,"sw,Enable charging":False,"sl,Breaker":6}
        self.apiConfig = {'sw,Enable balancing':False,"sw,Enable charging":False,"sl,Breaker":6}
        self.SETTING_PROFILES = 'setting.dat'

    
    def update_Config(self):
        try:
            setting = self.read_setting()
        except OSError:
            setting = {}
        
        for i in self.config: 
            if i in setting:
                if (self.config[i] != setting[i]):
                    self.config[i] = setting[i]
                    print("Ukldadam")
            else:
                setting[i] = self.config[i]
                self.write_setting(setting)
        
        
        
            
    def handle_configure(self,variable, value):
        if len(variable)>0:
            try:
                setting = self.read_setting()
            except OSError:
                setting = {}

            setting[variable] = value
            print(variable,value)
            self.write_setting(setting)
            time.sleep(1)
            self.update_Config()
            return True
        
        else:
            return False

        
    def read_setting(self):
        with open(self.SETTING_PROFILES) as f:
            lines = f.readlines()
            f.close()
        setting = {}
        for line in lines:
            variable, value = line.strip("\n").split(";")
            setting[variable] = value
        
        return setting


    def write_setting(self,setting):
        lines = []
        for variable, value in setting.items():
            lines.append("%s;%s\n" % (variable, value))
        with open(self.SETTING_PROFILES, "w") as f:
            f.write(''.join(lines))
            f.close()