import json
from gc import collect
import ulogging
collect()

FAST = 1
ECO = 0


class Evse:

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
        self.__last_charge_mode = self.setting.config["chargeMode"]
        self.logger = ulogging.getLogger("Evse")

        if int(self.setting.config['sw,TESTING SOFTWARE']) == 1:
            self.logger.setLevel(ulogging.DEBUG)
        else:
            self.logger.setLevel(ulogging.INFO)

    async def evse_handler(self):
        status = []
        self.__check_charge_mode_change()
        self.data_layer.data['NUMBER_OF_EVSE'] = int(self.setting.config["in,EVSE-NUMBER"])
        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            try:
                status.append(await self.__read_evse_data(1000, 3, _id=(i + 1)))
            except Exception as e:
                status.append('FAILED_READ')
                self.logger.info("evse_handler with ID: {} has error: {}".format((i + 1), e))
        current = self.balancingEvseCurrent()
        hdo_max_current = int(self.setting.config['in,AC-IN-MAX-CURRENT-FROM-GRID-A'])
        if hdo_max_current > current:
            hdo_max_current = current
        current_contribution = self.current_evse_contribution(current)
        write_errors = []
        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            try:
                if status[i] == 'SUCCESS_READ':

                    self.logger.debug("EVSE:{} with current: {}".format(i + 1, current))
                    if self.setting.config["sw,ENABLE CHARGING"] == '1':
                        if (self.setting.config["sw,WHEN AC IN: CHARGING"] == '1') and int(self.setting.config["chargeMode"]) == ECO:
                            if self.wattmeter.data_layer.data["A"] == 1:
                                async with self.evse_interface as e:
                                    await e.writeEvseRegister(1000, [hdo_max_current], i + 1)
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
                write_errors.append("ID {}: {}".format((i + 1), e))
        if write_errors:
            raise Exception("evse_handler error: {}".format("; ".join(write_errors)))
        return "Read: {}".format(status)

    def __check_charge_mode_change(self):
        charge_mode = self.setting.config["chargeMode"]
        if charge_mode != self.__last_charge_mode:
            self.logger.info("Charge mode changed from {} to {}, regulation reset".format(self.__last_charge_mode, charge_mode))
            self.__last_charge_mode = charge_mode
            self.__request_current = 0
            self.__cnt_current = 0
            self.__regulation_delay = 0
            self.regulation_lock = False
            self.lock_counter = 0

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
                    if self.data_layer.data["EV_COMM_ERR"][_id - 1] > 10:
                        self.data_layer.data["ACTUAL_CONFIG_CURRENT"][_id - 1] = 0
                        self.data_layer.data["ACTUAL_OUTPUT_CURRENT"][_id - 1] = 0
                        self.data_layer.data["EV_STATE"][_id - 1] = 0
                        self.data_layer.data["EV_COMM_ERR"][_id - 1] = 11

            raise Exception("__readEvse_data error: {}".format(e))

    def balancingEvseCurrent(self):
        delta = 0

        i1 = self.wattmeter.data_layer.data["I1"]
        if i1 > 32767:
            i1 -= 65536

        i2 = self.wattmeter.data_layer.data["I2"]
        if i2 > 32767:
            i2 -= 65536

        i3 = self.wattmeter.data_layer.data["I3"]
        if i3 > 32767:
            i3 -= 65536

        max_current = int(round(max(i1, i2, i3) / 100.0))

        sum_current = i1 + i2 + i3
        avg_current = int(round(sum_current / 300))
        grid_assist = int(self.setting.config["in,PV-GRID-ASSIST-A"])
        if grid_assist == 0:
            grid_assist = -1

        hdo = False
        if (1 == self.wattmeter.data_layer.data["A"]) and (1 == int(self.setting.config['sw,WHEN AC IN: CHARGING'])):
            hdo = True

        if (self.setting.config["btn,PHOTOVOLTAIC"] == '1') and (hdo == False) and (
                int(self.setting.config["chargeMode"]) == ECO):
            delta = grid_assist - int(round(i1 / 100.0))

        elif (self.setting.config["btn,PHOTOVOLTAIC"] == '2') and (hdo == False) and (
                int(self.setting.config["chargeMode"]) == ECO):
            delta = grid_assist - avg_current

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

        if delta < 0 and self.__cnt_current % 2 == 0:
            if '0' == self.setting.config["btn,PHOTOVOLTAIC"]:
                self.regulation_lock = True
                self.lock_counter = 1
                self.__request_current = self.__request_current + delta
            else:
                self.__request_current = self.__request_current - 1
                if self.__request_current < 6:
                    self.regulation_lock = True
                    self.lock_counter = 1
            self.__cnt_current = 0

        elif self.__regulation_delay > 0:
            self.__request_current = 0
            self.__cnt_current = 0

        elif not self.regulation_lock and self.__cnt_current % 3 == 0 and delta >= 0:
            if delta >= 6 and self.check_if_ev_is_connected():
                 self.__request_current = self.__request_current + 1
            elif self.check_if_ev_is_charging():
                self.__request_current = self.__request_current + 1
            self.__cnt_current = 0

        if self.__cnt_current >= 3:
            self.__cnt_current = 0

        if self.lock_counter >= 30:
            self.lock_counter = 0
            self.regulation_lock = False

        if (self.regulation_lock == True) or (self.lock_counter > 0):
            self.lock_counter = self.lock_counter + 1

        if self.__regulation_delay > 0:
            self.__regulation_delay = self.__regulation_delay + 1
        if self.setting.config["btn,PHOTOVOLTAIC"] == '0':
            if self.__regulation_delay > 60:
                self.__regulation_delay = 0
        elif self.__regulation_delay > 10:
            self.__regulation_delay = 0

        total_limit = 0
        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            total_limit += int(self.setting.config["inp,EVSE{}".format(i + 1)])

        if self.__request_current > total_limit:
            self.__request_current = total_limit

        if self.__request_current < 0:
            self.__request_current = 0
        return self.__request_current

    def current_evse_contribution(self, current):
        connected_evse = 0
        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            if self.data_layer.data["EV_STATE"][i] >= 2:  # pripojen nebo nabiji
                connected_evse += 1

        pom = 0
        if connected_evse != 0:
            pom = current / connected_evse

        length = connected_evse
        contribution_current = [0] * self.data_layer.data['NUMBER_OF_EVSE']
        for i in range(self.data_layer.data['NUMBER_OF_EVSE'], 0, -1):
            if self.data_layer.data["EV_STATE"][i - 1] >= 2:
                if pom < 6:
                    length -= 1
                    contribution_current[i - 1] = 0
                    if length != 0:
                        pom = current / length
                else:
                    contribution_current[i - 1] = int(pom)

        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            evse_limit = int(self.setting.config["inp,EVSE{}".format(i + 1)])
            if contribution_current[i] > evse_limit:
                contribution_current[i] = evse_limit
            yield contribution_current[i]

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
