import bootloader
from collections import OrderedDict
import os
from gc import collect
collect()

_SWITCH_ON = ('1', 'true', 'on', 'yes')
_SWITCH_OFF = ('0', 'false', 'off', 'no')
_LOG_CFG = "cfg:"


def parse_switch(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    try:
        text = str(value).strip().lower()
    except Exception:
        return default
    if text in _SWITCH_ON:
        return True
    if text in _SWITCH_OFF:
        return False
    try:
        return int(float(text)) != 0
    except Exception:
        return default


def normalize_value(variable, value):
    if isinstance(value, bool):
        text = '1' if value else '0'
    else:
        text = str(value).strip()

    if variable.startswith('sw,') or variable == 'DHCP':
        low = text.lower()
        if low in _SWITCH_ON:
            return '1'
        if low in _SWITCH_OFF:
            return '0'
        try:
            return '1' if int(float(text)) != 0 else '0'
        except Exception:
            return None

    if (';' in text) or ('\n' in text) or ('\r' in text):
        return None
    return text


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
        self.defaults = {}
        for key in self.config:
            self.defaults[key] = self.config[key]
        self.SETTING_PROFILES = 'setting.dat'
        self.SETTING_TMP = 'setting.dat.tmp'
        self.handle_configure('txt,ACTUAL SW VERSION', self.boot.get_version(""))

    def get_switch(self, variable, default=False):
        return parse_switch(self.config.get(variable), default)

    def getConfig(self):
        setting = {}
        try:
            setting = self.read_setting()
        except OSError:
            setting = {}

        if len(setting) != len(self.config):
            for i in self.config:
                if i in setting:
                    if self.config[i] != setting[i]:
                        self.config[i] = setting[i]
            setting = {}

        setting_changed = False
        for i in self.config:
            if i in setting:
                if self.config[i] != setting[i]:
                    self.config[i] = setting[i]
            else:
                setting[i] = self.config[i]
                setting_changed = True
        fixed = False
        for i in self.config:
            if i.startswith('sw,') or i == 'DHCP':
                default = parse_switch(self.defaults.get(i), False)
                canonical = '1' if parse_switch(self.config[i], default) else '0'
                if self.config[i] != canonical:
                    print(_LOG_CFG, 'fix', i, canonical)
                    self.config[i] = canonical
                    setting[i] = canonical
                    fixed = True

        if setting_changed or fixed:
            self.write_setting(setting)

        if self.config['ID'] == '0':
            id = bytearray(os.urandom(4))
            randId = ''
            for i in range(0,len(id)):
                randId+= str((int(id[i])))
            self.config['ID'] = randId[-5:]
            self.handle_configure('ID', self.config['ID'])

        return self.config

    def handle_configure(self,variable, value):
        try:
            if variable is None or len(variable) == 0:
                return False

            new_value = normalize_value(variable, value)
            if new_value is None:
                print(_LOG_CFG, 'bad', variable)
                return False

            self.handleDifferentRequests(variable, new_value)

            try:
                setting = self.read_setting()
            except OSError:
                setting = {}

            if setting.get(variable) != new_value:
                setting[variable] = new_value
                self.write_setting(setting)
                self.getConfig()
            elif self.config.get(variable) != new_value:
                self.config[variable] = new_value

            return self.config.get(variable) == new_value
        except Exception as e:
            print(_LOG_CFG, 'err', e)
            return False

    def handleDifferentRequests(self,variable,value):
        if variable == 'bt,RESET WATTMETER':
            from machine import reset
            reset()

    def _parse_setting(self, path):
        setting = {}
        with open(path) as f:
            for line in f:
                line = line.strip("\n").strip("\r")
                if len(line) == 0:
                    continue
                try:
                    variable, value = line.split(";", 1)
                except ValueError:
                    print(_LOG_CFG, 'line')
                    continue
                setting[variable] = value
        return setting

    def read_setting(self):
        try:
            return self._parse_setting(self.SETTING_PROFILES)
        except OSError:
            return self._parse_setting(self.SETTING_TMP)

    def write_setting(self,setting):
        with open(self.SETTING_TMP, "w") as f:
            for variable, value in setting.items():
                f.write(variable)
                f.write(';')
                f.write(str(value))
                f.write('\n')
        try:
            os.remove(self.SETTING_PROFILES)
        except OSError:
            pass
        os.rename(self.SETTING_TMP, self.SETTING_PROFILES)
