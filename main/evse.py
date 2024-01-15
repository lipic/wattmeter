import json
from gc import collect
import ulogging
collect()


class Evse():

    def __init__(self, wattmeter, evse, __config__):
        self.evse_interface = evse
        self.data_layer = DataLayer()
        self.setting = __config__
        self.wattmeter = wattmeter
        self.regulation_lock = False
        self.lock_counter = 0
        self.__regulation_delay = 0
        self.__cnt_current = 0
        self.__request_current = 0
        self.logger = ulogging.getLogger("Evse")

        if int(self.setting.config['sw,TESTING SOFTWARE']) == 1:
            self.logger.setLevel(ulogging.DEBUG)
        else:
            self.logger.setLevel(ulogging.INFO)

    async def evse_handler(self):
        state = ""
        status = []
        self.data_layer.data['NUMBER_OF_EVSE'] = int(self.setting.config["in,EVSE-NUMBER"])
        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            try:
                status.append(await self.__read_evse_data(1000, 3, _id=(i + 1)))
            except Exception as e:
                self.logger.info("evse_handler with ID: {} has error: {}".format((i + 1), e))
        current = self.balancingEvseCurrent()
        current_contribution = self.current_evse_contribution(current)
        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            try:
                if status[i] == 'SUCCESS_READ':

                    self.logger.debug("EVSE:{} with current: {}".format(i + 1, current))
                    if self.setting.config["sw,ENABLE CHARGING"] == '1':
                        if (self.setting.config["sw,WHEN AC IN: CHARGING"] == '1') and self.setting.config["chargeMode"] == '0':
                            if self.wattmeter.data_layer.data["A"] == 1:
                                if self.setting.config["sw,ENABLE BALANCING"] == '1':
                                    current = next(current_contribution)
                                    async with self.evse_interface as e:
                                        await e.writeEvseRegister(1000, [current], i + 1)
                                else:
                                    current = int(self.setting.config["inp,EVSE{}".format(i + 1)])
                                    async with self.evse_interface as e:
                                        await e.writeEvseRegister(1000, [current], i + 1)
                            else:
                                async with self.evse_interface as e:
                                    await e.writeEvseRegister(1000, [0], i + 1)
                        else:
                            if self.setting.config["sw,ENABLE BALANCING"] == '1':
                                current = next(current_contribution)
                                async with self.evse_interface as e:
                                    await e.writeEvseRegister(1000, [current], i + 1)
                            else:
                                current = int(self.setting.config["inp,EVSE{}".format(i + 1)])
                                async with self.evse_interface as e:
                                    await e.writeEvseRegister(1000, [current], i + 1)
                    else:
                        async with self.evse_interface as e:
                            await e.writeEvseRegister(1000, [0], i + 1)
            except Exception as e:
                raise Exception("evse_handler error: {}".format(e))
        return "Read: {}; Write: {}".format(status, state)

    async def __read_evse_data(self, reg, length, _id):
        try:
            async with self.evse_interface as e:
                receive_data = await e.readEvseRegister(reg, length, _id)

            if reg == 1000 and (receive_data != "Null") and receive_data:
                if len(self.data_layer.data["ACTUAL_CONFIG_CURRENT"]) < _id:
                    self.data_layer.data["ACTUAL_CONFIG_CURRENT"].append(int(((receive_data[0]) << 8) | receive_data[1]))
                    self.data_layer.data["ACTUAL_OUTPUT_CURRENT"].append(int(((receive_data[2]) << 8) | receive_data[3]))
                    self.data_layer.data["EV_STATE"].append(int(((receive_data[4]) << 8) | receive_data[5]))
                    self.data_layer.data["EV_COMM_ERR"].append(0)
                else:
                    self.data_layer.data["ACTUAL_CONFIG_CURRENT"][_id - 1] = int(
                        ((receive_data[0]) << 8) | receive_data[1])
                    self.data_layer.data["ACTUAL_OUTPUT_CURRENT"][_id - 1] = int(
                        ((receive_data[2]) << 8) | receive_data[3])
                    self.data_layer.data["EV_STATE"][_id - 1] = int(((receive_data[4]) << 8) | receive_data[5])
                    self.data_layer.data["EV_COMM_ERR"][_id - 1] = 0
                return 'SUCCESS_READ'

            else:
                return "Timed out waiting for result."

        except Exception as e:
            if reg == 1000:
                if len(self.data_layer.data["EV_COMM_ERR"]) < _id:
                    self.data_layer.data["EV_COMM_ERR"].append(0)
                    self.data_layer.data["ACTUAL_CONFIG_CURRENT"].append(0)
                    self.data_layer.data["ACTUAL_OUTPUT_CURRENT"].append(0)
                    self.data_layer.data["EV_STATE"].append(0)
                else:
                    self.data_layer.data["EV_COMM_ERR"][_id - 1] += 1
                    if self.data_layer.data["EV_COMM_ERR"][_id - 1] > 30:
                        self.data_layer.data["ACTUAL_CONFIG_CURRENT"][_id - 1] = 0
                        self.data_layer.data["ACTUAL_OUTPUT_CURRENT"][_id - 1] = 0
                        self.data_layer.data["EV_STATE"][_id - 1] = 0
                        self.data_layer.data["EV_COMM_ERR"][_id - 1] = 31

            raise Exception("__readEvse_data error: {}".format(e))

    def balancingEvseCurrent(self):
        i1 = 0
        i2 = 0
        i3 = 0
        max_current = 0
        delta = 0

        if self.wattmeter.data_layer.data["I1"] > 32767:
            i1 = self.wattmeter.data_layer.data["I1"] - 65535
        else:
            i1 = self.wattmeter.data_layer.data["I1"]

        if self.wattmeter.data_layer.data["I2"] > 32767:
            i2 = self.wattmeter.data_layer.data["I2"] - 65535
        else:
            i2 = self.wattmeter.data_layer.data["I2"]

        if self.wattmeter.data_layer.data["I3"] > 32767:
            i3 = self.wattmeter.data_layer.data["I3"] - 65535
        else:
            i3 = self.wattmeter.data_layer.data["I3"]

        if (i1 > i2) and (i1 > i3):
            max_current = int(round(i1 / 100.0))

        if (i2 > i1) and (i2 > i3):
            max_current = int(round(i2 / 100.0))

        if (i3 > i1) and (i3 > i2):
            max_current = int(round(i3 / 100.0))

        sum_current = i1 + i2 + i3
        avg_current = int(round(sum_current / 300))

        hdo = False
        if (1 == self.wattmeter.data_layer.data["A"]) and (1 == int(self.setting.config['sw,WHEN AC IN: CHARGING'])):
            hdo = True

        if (self.setting.config["btn,PHOTOVOLTAIC"] == '1') and (hdo == False) and (
                self.setting.config["chargeMode"] == '0'):
            delta = int(self.setting.config["in,PV-GRID-ASSIST-A"]) - int(round(i1 / 100.0))

        elif (self.setting.config["btn,PHOTOVOLTAIC"] == '2') and (hdo == False) and (
                self.setting.config["chargeMode"] == '0'):
            delta = int(self.setting.config["in,PV-GRID-ASSIST-A"]) - avg_current

        else:
            delta = int(self.setting.config["in,MAX-CURRENT-FROM-GRID-A"]) - max_current

        if max_current > int(self.setting.config["in,MAX-CURRENT-FROM-GRID-A"]):
            delta = int(self.setting.config["in,MAX-CURRENT-FROM-GRID-A"]) - max_current

        self.__cnt_current = self.__cnt_current + 1
        # Dle normy je zmena proudu EV nasledujici po zmene pracovni cyklu PWM maximalne 5s
        breaker = int(self.setting.config["in,MAX-CURRENT-FROM-GRID-A"])
        if (breaker * 0.5 + delta) < 0:
            self.__request_current = 0
            self.__regulation_delay = 1

        elif self.__cnt_current >= 2:
            if delta < 0:
                self.__request_current = self.__request_current + delta
                self.regulation_lock = True
                self.lock_counter = 1

            elif self.__regulation_delay > 0:
                self.__request_current = 0

            elif not self.regulation_lock:
                if delta >= 6 and self.check_if_ev_is_connected():
                    self.__request_current = self.__request_current + 1
                elif self.check_if_ev_is_charging():
                    self.__request_current = self.__request_current + 1
                else:
                    pass

            self.__cnt_current = 0

        # print("self.regulationLock1",self.regulationLock1)
        if self.lock_counter >= 30:
            self.lock_counter = 0
            self.regulation_lock = False

        if (self.regulation_lock == True) or (self.lock_counter > 0):
            self.lock_counter = self.lock_counter + 1

        if self.__regulation_delay > 0:
            self.__regulation_delay = self.__regulation_delay + 1
        if self.__regulation_delay > 60:
            self.__regulation_delay = 0
        sum = 0
        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            sum += int(self.setting.config["inp,EVSE{}".format(i + 1)])

        if self.__request_current > sum:
            self.__request_current = sum

        # print("Request current: {}A".format(self.__requestCurrent))
        if self.__request_current < 0:
            self.__request_current = 0
        return self.__request_current

    def current_evse_contribution(self, current):
        active_evse = 0
        connected_evse = 0

        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            if self.data_layer.data["EV_STATE"][i] == 3:
                active_evse += 1
            if self.data_layer.data["EV_STATE"][i] >= 2:  # pripojen nebo nabiji
                connected_evse += 1

        if active_evse == 0:
            active_evse = 1

        pom = 0
        if connected_evse != 0:
            pom = current / connected_evse

        length = connected_evse
        contibutin_current = [i for i in range(0, self.data_layer.data['NUMBER_OF_EVSE'])]
        for i in range(self.data_layer.data['NUMBER_OF_EVSE'], 0, -1):
            if self.data_layer.data["EV_STATE"][i - 1] >= 2:
                if pom < 6:
                    length -= 1
                    contibutin_current[i - 1] = 0
                    if length != 0:
                        pom = current / length
                else:
                    contibutin_current[i - 1] = int(pom)

            else:
                contibutin_current[i - 1] = 0

        i = 0
        while i < self.data_layer.data['NUMBER_OF_EVSE']:
            if contibutin_current[i] > int(self.setting.config["inp,EVSE{}".format(i + 1)]):
                contibutin_current[i] = int(self.setting.config["inp,EVSE{}".format(i + 1)])
            yield contibutin_current[i]
            i += 1

    def check_if_ev_is_connected(self):
        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            if self.data_layer.data["EV_STATE"][i] == 2:
                return True
        return False

    def check_if_ev_is_charging(self):
        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            if self.data_layer.data["EV_STATE"][i] == 3:
                return True
        return False


class DataLayer:
    def __str__(self):
        return json.dumps(self.data)

    def __init__(self):
        self.data = {}
        self.data["ACTUAL_CONFIG_CURRENT"] = []
        self.data["ACTUAL_OUTPUT_CURRENT"] = []
        self.data["EV_STATE"] = []
        self.data["EV_COMM_ERR"] = []
        self.data["NUMBER_OF_EVSE"] = 0
