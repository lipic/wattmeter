import ujson as json
import time
from machine import Pin, UART
from gc import collect
import ulogging
collect()

class Wattmeter:

    def __init__(self, wattmeter, setting):
        self.relay = Pin(25, Pin.OUT)
        self.wattmeter_interface = wattmeter
        self.data_layer = DataLayer()
        self.file_handler = FileHandler()
        self.daily_consumption = 'daily_consumption.dat'
        self.time_init = False
        self.time_offset = False
        self.last_minute = 0
        self.last_hour = 0
        self.last_day = 0
        self.last_month = 0
        self.last_year = 0
        self.test = 0
        self.start_up_time = 0
        self.setting = setting
        self.e15_p_lock_counter = 0
        self.e15_p_lock = False
        self.minute_energy = []
        self.data_layer.data['ID'] = self.setting.config['ID']

        self.logger = ulogging.getLogger("Wattmeter")

        if int(self.setting.config['sw,TESTING SOFTWARE']) == 1:
            self.logger.setLevel(ulogging.DEBUG)
        else:
            self.logger.setLevel(ulogging.INFO)

    async def wattmeter_handler(self):
        if (self.time_offset is False) and self.time_init:
            self.start_up_time = time.time()
            self.last_minute = int(time.localtime()[4])
            self.last_day = int(time.localtime()[2])
            self.last_month = int(time.localtime()[1])
            self.last_year = int(time.localtime()[0])
            self.data_layer.data['D'] = self.file_handler.read_data(self.daily_consumption)
            self.data_layer.data["M"] = self.file_handler.get_monthly_energy(self.daily_consumption)
            self.time_offset = True

        self.data_layer.data['BREAKER'] = self.setting.config['in,MAX-CURRENT-FROM-GRID-A']
        self.data_layer.data['RUN_TIME'] = int(time.time() - self.start_up_time)
        current_year = str(time.localtime()[0])[-2:]
        self.data_layer.data['WATTMETER_TIME'] = (
            "{0:02}.{1:02}.{2}  {3:02}:{4:02}:{5:02}".format(time.localtime()[2], time.localtime()[1], current_year,
                                                             time.localtime()[3], time.localtime()[4],
                                                             time.localtime()[5]))

        await self.__read_wattmeter_data(1000, 12)
        await self.__read_wattmeter_data(2502, 6)
        await self.__read_wattmeter_data(2802, 6)
        await self.__read_wattmeter_data(3102, 12)
        await self.__read_wattmeter_data(2902, 6)
        await self.__read_wattmeter_data(1015, 3)
        await self.__read_wattmeter_data(4000, 12)
        await self.__read_wattmeter_data(200, 1)

        if self.setting.config['sw,P-E15-GUARD'] == '1':
            self.e15_p_protection()
        else:
            self.control_relay()

        if self.last_minute != int(time.localtime()[4]):

            if len(self.data_layer.data["Pm"]) < 61:
                self.data_layer.data["Pm"].append(self.data_layer.data['Em'] * 6)
            else:
                self.data_layer.data["Pm"] = self.data_layer.data["Pm"][1:]
                self.data_layer.data["Pm"].append(self.data_layer.data['Em'] * 6)

            self.data_layer.data["Pm"][0] = len(self.data_layer.data["Pm"])
            async with self.wattmeter_interface as w:
                await w.writeWattmeterRegister(100, [1])

            self.last_minute = int(time.localtime()[4])

            if self.last_minute % 15 == 0:
                self.e15_p_lock = False
                self.minute_energy.clear()
                self.logger.debug("reset e15_p_lock and clear minute_energy={}".format(self.minute_energy))

            self.minute_energy.append(int(self.data_layer.data['Em']/10))

        if self.time_init:
            if self.last_hour != int(time.localtime()[3]):
                status = await self.__read_wattmeter_data(100, 1)

                async with self.wattmeter_interface as w:
                    await w.writeWattmeterRegister(101, [1])
                self.last_hour = int(time.localtime()[3])
                if len(self.data_layer.data["Es"]) < 97:
                    self.data_layer.data["Es"].append(self.last_hour)
                    self.data_layer.data["Es"].append(self.data_layer.data['Eh'])
                    self.data_layer.data["Es"].append(self.data_layer.data['En'])
                    self.data_layer.data["Es"].append(self.data_layer.data['A'])
                else:
                    self.data_layer.data["Es"] = self.data_layer.data["Es"][4:]
                    self.data_layer.data["Es"].append(self.last_hour)
                    self.data_layer.data["Es"].append(self.data_layer.data['Eh'])
                    self.data_layer.data["Es"].append(self.data_layer.data['En'])
                    self.data_layer.data["Es"].append(self.data_layer.data['A'])

                self.data_layer.data["Es"][0] = len(self.data_layer.data["Es"])

            else:
                if len(self.data_layer.data["Es"]) < 97:
                    self.data_layer.data["Es"][len(self.data_layer.data["Es"]) - 3] = self.data_layer.data['Eh']
                    self.data_layer.data["Es"][len(self.data_layer.data["Es"]) - 2] = self.data_layer.data['En']
                    self.data_layer.data["Es"][len(self.data_layer.data["Es"]) - 1] = self.data_layer.data['A']
                else:
                    self.data_layer.data["Es"][94] = self.data_layer.data['Eh']
                    self.data_layer.data["Es"][95] = self.data_layer.data['En']
                    self.data_layer.data["Es"][96] = self.data_layer.data['A']

        if (self.last_day != int(time.localtime()[2])) and self.time_init and self.time_offset:
            status = await self.__read_wattmeter_data(100, 1)
            day = {("{0:02}/{1:02}/{2}".format(self.last_month, self.last_day, str(self.last_year)[-2:])): [
                self.data_layer.data["E1dP"] + self.data_layer.data["E2dP"] + self.data_layer.data["E3dP"],
                self.data_layer.data["E1dN"] + self.data_layer.data["E2dN"] + self.data_layer.data["E3dN"]]}
            async with self.wattmeter_interface as w:
                await w.writeWattmeterRegister(102, [1])

            self.last_year = int(time.localtime()[0])
            self.last_month = int(time.localtime()[1])
            self.last_day = int(time.localtime()[2])
            self.file_handler.write_data(self.daily_consumption, day)
            self.data_layer.data["D"] = self.file_handler.read_data(self.daily_consumption, 31)
            self.data_layer.data["M"] = self.file_handler.get_monthly_energy(self.daily_consumption)

    async def __read_wattmeter_data(self, reg, length):

        try:
            async with self.wattmeter_interface as w:
                receive_data = await w.readWattmeterRegister(reg, length)

            if (receive_data != "Null") and (reg == 1000):
                self.data_layer.data['I1'] = int(((receive_data[0]) << 8) | (receive_data[1]))
                self.data_layer.data['I2'] = int(((receive_data[2]) << 8) | (receive_data[3]))
                self.data_layer.data['I3'] = int(((receive_data[4]) << 8) | (receive_data[5]))
                self.data_layer.data['U1'] = int(((receive_data[6]) << 8) | (receive_data[7]))
                self.data_layer.data['U2'] = int(((receive_data[8]) << 8) | (receive_data[9]))
                self.data_layer.data['U3'] = int(((receive_data[10]) << 8) | (receive_data[11]))
                self.data_layer.data['P1'] = int(((receive_data[12]) << 8) | (receive_data[13]))
                self.data_layer.data['P2'] = int(((receive_data[14]) << 8) | (receive_data[15]))
                self.data_layer.data['P3'] = int(((receive_data[16]) << 8) | (receive_data[17]))
                self.data_layer.data['S1'] = int(((receive_data[18]) << 8) | (receive_data[19]))
                self.data_layer.data['S2'] = int(((receive_data[20]) << 8) | (receive_data[21]))
                self.data_layer.data['S3'] = int(((receive_data[22]) << 8) | (receive_data[23]))
                return "SUCCESS_READ"

            if (receive_data != "Null") and (reg == 200):
                a = int(receive_data[0] << 8) | receive_data[1]
                if a == 1 and '1' == self.setting.config['sw,AC IN ACTIVE: HIGH']:
                    self.data_layer.data['A'] = 1
                elif a == 0 and '0' == self.setting.config['sw,AC IN ACTIVE: HIGH']:
                    self.data_layer.data['A'] = 1
                else:
                    self.data_layer.data['A'] = 0

                return "SUCCESS_READ"

            elif (receive_data != "Null") and (reg == 1015):
                self.data_layer.data['F1'] = int(((receive_data[0]) << 8) | (receive_data[1]))
                self.data_layer.data['F2'] = int(((receive_data[2]) << 8) | (receive_data[3]))
                self.data_layer.data['F3'] = int(((receive_data[4]) << 8) | (receive_data[5]))
                return "SUCCESS_READ"

            elif (receive_data != "Null") and (reg == 2502):
                self.data_layer.data['Em'] = int(((receive_data[0]) << 8) | receive_data[1]) + int(
                    ((receive_data[2]) << 8) | receive_data[3]) + int((receive_data[4] << 8) | receive_data[5]) - int(
                    (receive_data[6] << 8) | receive_data[7]) - int((receive_data[8] << 8) | receive_data[9]) - int(
                    (receive_data[10] << 8) | receive_data[11])
                return "SUCCESS_READ"

            elif (receive_data != "Null") and (reg == 2802):
                self.data_layer.data['Eh'] = int(((receive_data[0]) << 8) | (receive_data[1])) + int(
                    ((receive_data[2]) << 8) | receive_data[3]) + int(((receive_data[4]) << 8) | receive_data[5])
                self.data_layer.data['En'] = int(((receive_data[6]) << 8) | (receive_data[7])) + int(
                    ((receive_data[8]) << 8) | receive_data[9]) + int(((receive_data[10]) << 8) | receive_data[11])
                return "SUCCESS_READ"

            elif (receive_data != "Null") and (reg == 3102):

                self.data_layer.data["E1dP"] = int((receive_data[0] << 8) | receive_data[1])
                self.data_layer.data["E2dP"] = int((receive_data[2] << 8) | receive_data[3])
                self.data_layer.data["E3dP"] = int((receive_data[4] << 8) | receive_data[5])
                self.data_layer.data["E1dN"] = int((receive_data[6] << 8) | receive_data[7])
                self.data_layer.data["E2dN"] = int((receive_data[8] << 8) | receive_data[9])
                self.data_layer.data["E3dN"] = int((receive_data[10] << 8) | receive_data[11])
                self.data_layer.data['W1'] = int(((receive_data[12]) << 8) | receive_data[13])
                self.data_layer.data['W2'] = int(((receive_data[14]) << 8) | receive_data[15])
                self.data_layer.data['W3'] = int(((receive_data[16]) << 8) | receive_data[17])
                self.data_layer.data['R1'] = int(((receive_data[18]) << 8) | receive_data[19])
                self.data_layer.data['R2'] = int(((receive_data[20]) << 8) | receive_data[21])
                self.data_layer.data['R3'] = int(((receive_data[22]) << 8) | receive_data[23])
                return "SUCCESS_READ"

            elif (receive_data != "Null") and (reg == 4000):

                self.data_layer.data["E1tP"] = int(
                    (receive_data[2] << 24) | (receive_data[3] << 16) | (receive_data[0] << 8) | receive_data[1])
                self.data_layer.data["E2tP"] = int(
                    (receive_data[6] << 24) | (receive_data[7] << 16) | (receive_data[4] << 8) | receive_data[5])
                self.data_layer.data["E3tP"] = int(
                    (receive_data[10] << 24) | (receive_data[11] << 16) | (receive_data[8] << 8) | receive_data[9])
                self.data_layer.data["E1tN"] = int(
                    (receive_data[14] << 24) | (receive_data[15] << 16) | (receive_data[12] << 8) | receive_data[13])
                self.data_layer.data["E2tN"] = int(
                    (receive_data[18] << 24) | (receive_data[19] << 16) | (receive_data[16] << 8) | receive_data[17])
                self.data_layer.data["E3tN"] = int(
                    (receive_data[22] << 24) | (receive_data[23] << 16) | (receive_data[20] << 8) | receive_data[21])

                return "SUCCESS_READ"

            elif (receive_data != "Null") and (reg == 2902):

                self.data_layer.data["EpDP"] = int(((receive_data[0]) << 8) | receive_data[1]) + int(
                    ((receive_data[2]) << 8) | receive_data[3]) + int(((receive_data[4]) << 8) | receive_data[5])
                self.data_layer.data["EpDN"] = int(((receive_data[6]) << 8) | receive_data[7]) + int(
                    ((receive_data[8]) << 8) | receive_data[9]) + int(((receive_data[10]) << 8) | receive_data[11])
                return "SUCCESS_READ"

            else:
                return "Timed out waiting for result."

        except Exception as e:
            return "Exception: {}. UART is probably not connected.".format(e)

    def e15_p_protection(self):

        if self.e15_p_lock is False:
            max_p = int(self.setting.config['in,MAX-P-KW'])*1000
            max_e15 = int(int(self.setting.config['in,MAX-E15-KWH']) * 100)
            p1 = self.data_layer.data['P1'] - 65535 if self.data_layer.data['P1'] > 32767 else self.data_layer.data['P1']
            p2 = self.data_layer.data['P2'] - 65535 if self.data_layer.data['P2'] > 32767 else self.data_layer.data['P2']
            p3 = self.data_layer.data['P3'] - 65535 if self.data_layer.data['P3'] > 32767 else self.data_layer.data['P3']
            sum_p = sum([p1, p2, p3])

            e15 = self.minute_energy
            total_energy = 0

            for minute_energy in e15:
                total_energy += minute_energy

            self.logger.debug("total_energy={}Wh; max_e15={}Wh; max_p={}W; sum_p= {}W".format(total_energy, max_e15, max_p, sum_p))
            if (total_energy < (-max_e15)) or (sum_p < -max_p):
                self.logger.debug("Relay off")
                self.relay.off()
                self.data_layer.data["RELAY"] = 0
                self.e15_p_lock = True
            else:
                self.logger.debug("Relay on")
                self.relay.on()
                self.data_layer.data["RELAY"] = 1

        else:
            self.logger.debug("e15_p_lock_counter={}".format(self.e15_p_lock_counter))
            self.e15_p_lock_counter += 1
            self.relay.off()
            if self.e15_p_lock_counter > 40:  # 60 -> 1 minute
                self.e15_p_lock = False
                self.e15_p_lock_counter = 0

    def negotiation_relay(self):
        if self.relay.value():
            self.relay.off()
            self.data_layer.data["RELAY"] = 0
            return False
        else:
            self.relay.on()
            self.data_layer.data["RELAY"] = 1
            return True

    def control_relay(self):
        if (self.setting.config['sw,WHEN OVERFLOW: RELAY ON']) == '1':
            i1_n = 0
            i2_n = 0
            i3_n = 0
            if self.data_layer.data["I1"] > 32767:
                i1_n = (self.data_layer.data["I1"] - 65535) / 100
            if self.data_layer.data["I2"] > 32767:
                i2_n = (self.data_layer.data["I2"] - 65535) / 100
            if self.data_layer.data["I3"] > 32767:
                i3_n = (self.data_layer.data["I3"] - 65535) / 100
            if (i1_n > 0) or (i2_n > 0) or (i3_n > 0):
                self.relay.on()
            else:
                self.relay.off()
        elif (self.setting.config['sw,WHEN AC IN: RELAY ON']) == '1':
            if self.data_layer.data['A'] == 1:
                self.relay.on()
            else:
                self.relay.off()
        if self.relay.value():
            self.data_layer.data["RELAY"] = 1
        else:
            self.data_layer.data["RELAY"] = 0


class DataLayer:
    def __str__(self):
        return json.dumps(self.data)

    def __init__(self):
        self.data = {}
        self.data['I1'] = 0  # I1
        self.data['I2'] = 0  # I2
        self.data['I3'] = 0  # I3
        self.data['U1'] = 0
        self.data['U2'] = 0
        self.data['U3'] = 0
        self.data['F1'] = 0  # power factor L1
        self.data['F2'] = 0  # power factor L2
        self.data['F3'] = 0  # power factor L3
        self.data['W1'] = 0  # positive power peak L1
        self.data['W2'] = 0  # positive power peak L2
        self.data['W3'] = 0  # positive power peak L3
        self.data['R1'] = 0  # negative power peak L1
        self.data['R2'] = 0  # negative power peak L2
        self.data['R3'] = 0  # negative power peak L3
        self.data['Em'] = 0  # Pavg per minute
        self.data['Eh'] = 0  # positive hour energy
        self.data['En'] = 0  # negative hour energy
        self.data['P1'] = 0
        self.data['P2'] = 0
        self.data['P3'] = 0
        self.data['S1'] = 0
        self.data['S2'] = 0
        self.data['S3'] = 0
        self.data['A'] = 0  # AC_IN
        self.data["Pm"] = [0]  # minute power
        self.data["Es"] = [0]  # Hour energy
        self.data['D'] = []  # Daily energy
        self.data['M'] = []  # Monthly energy
        self.data["E1dP"] = 0
        self.data["E2dP"] = 0
        self.data["E3dP"] = 0
        self.data["E1dN"] = 0
        self.data["E2dN"] = 0
        self.data["E3dN"] = 0
        self.data["EpDP"] = 0  # positive previous day Energy L1,L2,L3
        self.data["EpDN"] = 0  # negative previous day Energy L1,L2,L3
        self.data["E1tP"] = 0  # positive total Energy L1
        self.data["E2tP"] = 0  # positive total Energy L1
        self.data["E3tP"] = 0  # positive total Energy L1
        self.data["E1tN"] = 0  # negative total Energy L1
        self.data["E2tN"] = 0  # negative total Energy L1
        self.data["E3tN"] = 0  # negative total Energy L1
        self.data['RUN_TIME'] = 0
        self.data['WATTMETER_TIME'] = 0
        self.data['ID'] = 0
        self.data['BREAKER'] = 0


class FileHandler:

    def read_data(self, file, length=None):
        data = []
        try:
            csv_gen = self.csv_reader(file)
            row_count = 0
            data = []
            for row in csv_gen:
                collect()
                row_count += 1

            csv_gen = self.csv_reader(file)
            cnt = 0
            for i in csv_gen:
                cnt += 1
                if cnt > row_count - 31:
                    data.append(i.replace("\n", ""))
                collect()
            return data
        except Exception as e:
            return []

    def csv_reader(self, file_name):
        for row in open(file_name, "r"):
            try:
                yield row
            except StopIteration:
                return

    def get_monthly_energy(self, file):
        energy = []
        last_month = 0
        last_year = 0
        positive_energy = 0
        negative_energy = 0

        try:
            csv_gen = self.csv_reader(file)
            for line in csv_gen:
                line = line.replace("\n", "").replace("/", ":").replace("[", "").replace("]", "").replace(",",
                                                                                                          ":").replace(
                    " ", "").split(":")
                if last_month == 0:
                    last_month = int(line[0])
                    last_year = int(line[2])

                if last_month != int(line[0]):
                    if len(energy) < 36:
                        energy.append("{}/{}:[{},{}]".format(last_month, last_year, positive_energy, negative_energy))
                    else:
                        energy = energy[1:]
                        energy.append("{}/{}:[{},{}]".format(last_month, last_year, positive_energy, negative_energy))
                    positive_energy = 0
                    negative_energy = 0
                    last_month = int(line[0])
                    last_year = int(line[2])

                positive_energy += int(line[3])
                negative_energy += int(line[4])
                collect()

            if len(energy) < 36:
                energy.append("{}/{}:[{},{}]".format(last_month, last_year, positive_energy, negative_energy))
            else:
                energy = energy[1:]
                energy.append("{}/{}:[{},{}]".format(last_month, last_year, positive_energy, negative_energy))

            if energy is None:
                return []

            return energy

        except Exception as e:
            print("Error: ", e)

    def write_data(self, file, data):
        lines = []
        for variable, value in data.items():
            lines.append(("%s:%s\n" % (variable, value)).replace(" ", ""))

        with open(file, "a+") as f:
            f.write(''.join(lines))
