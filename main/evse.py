import json
from gc import collect
import ulogging
collect()

FAST = 1
ECO = 0

MIN_EVSE_CURRENT = 6           # minimalni nabijeci proud jedne stanice [A]
EVSE_START_MARGIN = 2          # hystereze: rezerva navic, aby se pripojilo dalsi EVSE [A]
EVSE_RESTART_HOLD_CYCLES = 20  # po odstaveni EVSE se dalsi nesmi pridat po tolik cyklu (~30 s)


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
        self.__last_written = {}
        self.__active_evse = 0
        self.__restart_hold = 0
        self.__last_lock = False
        self.__last_delay = 0
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
        charging_enabled = self.setting.config["sw,ENABLE CHARGING"] == '1'
        hdo_mode = (self.setting.config["sw,WHEN AC IN: CHARGING"] == '1') and int(
            self.setting.config["chargeMode"]) == ECO
        balancing = self.setting.config["sw,ENABLE BALANCING"] == '1'

        # Podily se pocitaji dopredu pro vsechny stanice a indexuji se cislem stanice.
        # Drive se pouzival generator, ktery se posouval jen u prectenych EVSE, takze pri
        # chybe cteni dostala stanice podil urceny pro jinou.
        contribution = None
        if charging_enabled and (not hdo_mode) and balancing:
            contribution = self.current_evse_contribution(current)

        write_errors = []
        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            try:
                if status[i] != 'SUCCESS_READ':
                    if self.logger.isEnabledFor(ulogging.DEBUG):
                        self.logger.debug("EVSE{} SKIP zapis, read status={}".format(i + 1, status[i]))
                    continue

                if charging_enabled:
                    if hdo_mode:
                        if self.wattmeter.data_layer.data["A"] == 1:
                            write_current = hdo_max_current
                        else:
                            write_current = 0
                        source = "HDO"
                    elif balancing:
                        write_current = contribution[i]
                        source = "BALANCE"
                    else:
                        write_current = int(self.setting.config["inp,EVSE{}".format(i + 1)])
                        source = "MANUAL"
                else:
                    write_current = 0
                    source = "CHARGING-OFF"

                self.__log_write(i + 1, write_current, source)
                async with self.evse_interface as e:
                    await e.writeEvseRegister(1000, [write_current], i + 1)
            except Exception as e:
                write_errors.append("ID {}: {}".format((i + 1), e))
        if write_errors:
            raise Exception("evse_handler error: {}".format("; ".join(write_errors)))
        return "Read: {}".format(status)

    def __log_write(self, evse_id, current, source):
        state = self.__data_at("EV_STATE", evse_id)
        cfg = self.__data_at("ACTUAL_CONFIG_CURRENT", evse_id)
        out = self.__data_at("ACTUAL_OUTPUT_CURRENT", evse_id)
        last = self.__last_written.get(evse_id)

        if last != current:
            self.__last_written[evse_id] = current
            if (last is not None) and ((last == 0) != (current == 0)):
                # Prave tady se nabijeni vypina / zapina - toto hledame v logu
                self.logger.info("EVSE{} {} {}A->{}A [{}] ev_state={} cfg={} out={} req={} lock={}/{} delay={}".format(
                    evse_id, "START" if current > 0 else "STOP", last, current, source,
                    state, cfg, out, self.__request_current,
                    self.regulation_lock, self.lock_counter, self.__regulation_delay))
            else:
                self.logger.info("EVSE{} SET {}A->{}A [{}] ev_state={} cfg={} out={}".format(
                    evse_id, last, current, source, state, cfg, out))
        elif self.logger.isEnabledFor(ulogging.DEBUG):
            self.logger.debug("EVSE{} HOLD {}A [{}] ev_state={} cfg={} out={}".format(
                evse_id, current, source, state, cfg, out))

    def __data_at(self, key, evse_id):
        if len(self.data_layer.data[key]) >= evse_id:
            return self.data_layer.data[key][evse_id - 1]
        return 0

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
            self.__active_evse = 0
            self.__restart_hold = 0

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
            delta_src = "PV-L1"

        elif (self.setting.config["btn,PHOTOVOLTAIC"] == '2') and (hdo == False) and (
                int(self.setting.config["chargeMode"]) == ECO):
            delta = grid_assist - avg_current
            delta_src = "PV-AVG"

        else:
            delta = int(self.setting.config["in,MAX-CURRENT-FROM-GRID-A"]) - max_current
            delta_src = "GRID"

        if max_current > int(self.setting.config["in,MAX-CURRENT-FROM-GRID-A"]):
            delta = int(self.setting.config["in,MAX-CURRENT-FROM-GRID-A"]) - max_current
            delta_src = "GRID-OVERLOAD"

        req_before = self.__request_current
        branch = "IDLE"
        self.__cnt_current = self.__cnt_current + 1
        # Dle normy je zmena proudu EV nasledujici po zmene pracovni cyklu PWM maximalne 5s
        breaker = int(self.setting.config["in,MAX-CURRENT-FROM-GRID-A"])
        if (breaker * 0.5 + delta) < 0:
            self.__request_current = 0
            if self.__regulation_delay == 0:  # logujeme jen vstup do stavu, ne kazdy cyklus
                self.logger.info("BAL PANIC-STOP: delta={} breaker={} -> request=0".format(delta, breaker))
            branch = "PANIC-STOP"
            self.__regulation_delay = 1

        if delta < 0 and self.__cnt_current % 2 == 0:
            if '0' == self.setting.config["btn,PHOTOVOLTAIC"]:
                self.regulation_lock = True
                self.lock_counter = 1
                self.__request_current = self.__request_current + delta
                branch = "DOWN-STEP(delta)"
            else:
                self.__request_current = self.__request_current - 1
                branch = "DOWN-1"
                if self.__request_current < 6:
                    self.regulation_lock = True
                    self.lock_counter = 1
                    branch = "DOWN-1+LOCK(req<6)"
            self.__cnt_current = 0

        elif self.__regulation_delay > 0:
            self.__request_current = 0
            self.__cnt_current = 0
            branch = "DELAY-HOLD-0"

        elif not self.regulation_lock and self.__cnt_current % 3 == 0 and delta >= 0:
            if delta >= 6 and self.check_if_ev_is_connected():
                 self.__request_current = self.__request_current + 1
                 branch = "UP-connected"
            elif self.check_if_ev_is_charging():
                self.__request_current = self.__request_current + 1
                branch = "UP-charging"
            else:
                branch = "UP-BLOCKED"
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
            branch = branch + "+CAP"
            self.__request_current = total_limit

        if self.__request_current < 0:
            self.__request_current = 0

        if self.regulation_lock != self.__last_lock:
            self.logger.info("BAL LOCK {} -> {} (lock_counter={}, req={}, delta={})".format(
                self.__last_lock, self.regulation_lock, self.lock_counter, self.__request_current, delta))
            self.__last_lock = self.regulation_lock
        if (self.__regulation_delay > 0) != (self.__last_delay > 0):
            self.logger.info("BAL DELAY {} -> {} (req={}, delta={})".format(
                self.__last_delay, self.__regulation_delay, self.__request_current, delta))
        self.__last_delay = self.__regulation_delay

        if req_before != self.__request_current:
            self.logger.info("BAL REQ {}A -> {}A [{}] src={} delta={} I=({}/{}/{})A max={} avg={} hdo={} pv={} mode={} limit={} lock={}/{} delay={}".format(
                req_before, self.__request_current, branch, delta_src, delta,
                int(round(i1 / 100.0)), int(round(i2 / 100.0)), int(round(i3 / 100.0)),
                max_current, avg_current, hdo,
                self.setting.config["btn,PHOTOVOLTAIC"], self.setting.config["chargeMode"],
                total_limit, self.regulation_lock, self.lock_counter, self.__regulation_delay))
        elif self.logger.isEnabledFor(ulogging.DEBUG):
            self.logger.debug("BAL req={}A [{}] src={} delta={} I=({}/{}/{})A max={} avg={} conn={} chrg={} cnt={} lock={}/{} delay={}".format(
                self.__request_current, branch, delta_src, delta,
                int(round(i1 / 100.0)), int(round(i2 / 100.0)), int(round(i3 / 100.0)),
                max_current, avg_current,
                self.check_if_ev_is_connected(), self.check_if_ev_is_charging(), self.__cnt_current,
                self.regulation_lock, self.lock_counter, self.__regulation_delay))
        return self.__request_current

    def __update_active_evse(self, current, connected):
        # Pocet aktivnich stanic se meni s hysterezi, aby regulacni zvlneni +-1 A
        # neprepinalo nabijeni porad dokola.
        #   dolu: hned, jakmile by nektera stanice dostala min nez MIN_EVSE_CURRENT
        #   nahoru: az kdyz je proud o EVSE_START_MARGIN vetsi nez holy minimum
        #           a zaroven uz vyprsel blokovaci cas po poslednim odstaveni
        if self.__restart_hold > 0:
            self.__restart_hold -= 1

        active = self.__active_evse
        reason = "KEEP"

        if active > connected:
            active = connected
            reason = "CLAMP-connected({})".format(connected)

        possible = int(current // MIN_EVSE_CURRENT)
        if possible > connected:
            possible = connected

        if possible < active:
            if active > 1:
                # blokace se tyka jen odstaveni druhe a dalsi stanice
                self.__restart_hold = EVSE_RESTART_HOLD_CYCLES
            active = possible
            reason = "DOWN"
        elif possible > active:
            if active == 0:
                # prvni stanice nabiha jako driv, bez hystereze i bez blokace
                active = 1
                reason = "UP-FIRST"
            else:
                need = MIN_EVSE_CURRENT * (active + 1) + EVSE_START_MARGIN
                if self.__restart_hold > 0:
                    reason = "UP-BLOCKED-HOLD"
                elif current < need:
                    reason = "UP-BLOCKED-MARGIN"
                else:
                    active += 1  # pridavame vzdy jen jednu stanici za cyklus
                    reason = "UP"

        self.__active_evse = active
        return active, reason

    def current_evse_contribution(self, current):
        connected = []
        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            if self.__data_at("EV_STATE", i + 1) >= 2:  # pripojen nebo nabiji
                connected.append(i)

        active_before = self.__active_evse
        active, reason = self.__update_active_evse(current, len(connected))

        share = 0
        if active > 0:
            share = int(current // active)

        contribution_current = [0] * self.data_layer.data['NUMBER_OF_EVSE']
        for i in connected[:active]:  # prednost maji stanice s nizsim cislem
            contribution_current[i] = share

        debug_on = self.logger.isEnabledFor(ulogging.DEBUG)
        caps = []
        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            evse_limit = int(self.setting.config["inp,EVSE{}".format(i + 1)])
            if contribution_current[i] > evse_limit:
                if debug_on:
                    caps.append("EVSE{}({}->{})".format(i + 1, contribution_current[i], evse_limit))
                contribution_current[i] = evse_limit

        if active != active_before:
            self.logger.info("SPLIT ACTIVE {} -> {} [{}] total={}A podil={}A connected={} ev_state={} hold={} -> {}".format(
                active_before, active, reason, current, share, len(connected),
                self.data_layer.data["EV_STATE"], self.__restart_hold, contribution_current))
        elif debug_on:
            self.logger.debug("SPLIT active={} [{}] total={}A podil={}A connected={} ev_state={} hold={} cap={} -> {}".format(
                active, reason, current, share, len(connected), self.data_layer.data["EV_STATE"],
                self.__restart_hold, caps, contribution_current))

        return contribution_current

    def check_if_ev_is_connected(self):
        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            if self.__data_at("EV_STATE", i + 1) == 2:
                return True
        return False

    def check_if_ev_is_charging(self):
        for i in range(0, self.data_layer.data['NUMBER_OF_EVSE']):
            if self.__data_at("EV_STATE", i + 1) == 3:
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
