import picoweb
from machine import reset, RTC
from time import time
import ujson as json
from gc import collect
import uasyncio as asyncio
collect()

class WebServerApp:
    def __init__(self, wlan, wattmeter, evse, watt_io, evse_io, setting):
        self.watt_io = watt_io
        self.evse_io = evse_io
        self.wifi_manager = wlan
        self.ip_address = self.wifi_manager.getIp()
        self.wattmeter = wattmeter
        self.evse = evse
        self.port = 8000
        self.datalayer = dict()
        self.setting = setting
        self.ROUTES = [
            ("/", self.main),
            ("/datatable", self.data_table),
            ("/overview", self.over_view),
            ("/updateWificlient", self.update_wificlient),
            ("/updateSetting", self.update_setting),
            ("/updateData", self.update_data),
            ("/updateEvse", self.update_evse),
            ("/settings", self.settings),
            ("/powerChart", self.power_chart),
            ("/energyChart", self.energy_chart),
            ("/getEspID", self.get_esp_id),
            ("/modbusRW", self.modbus_rw)
        ]
        self.app = picoweb.WebApp(None, self.ROUTES)

    def main(self, req, resp):
        collect()
        yield from picoweb.start_response(resp)
        yield from self.app.render_template(resp, "main.html")

    def over_view(self, req, resp):
        collect()
        yield from picoweb.start_response(resp)
        yield from self.app.render_template(resp, "overview.html")

    def settings(self, req, resp):
        collect()
        yield from picoweb.start_response(resp)
        yield from self.app.render_template(resp, "settings.html", (req,))

    def power_chart(self, req, resp):
        collect()
        yield from picoweb.start_response(resp)
        yield from self.app.render_template(resp, "powerChart.html", (req,))

    def energy_chart(self, req, resp):
        collect()
        yield from picoweb.start_response(resp)
        yield from self.app.render_template(resp, "energyChart.html", (req,))

    def modbus_rw(self, req, resp):
        collect()
        if req.method == "POST":
            datalayer = {}
            req = await self.proccess_msg(req)
            for i in req.form:
                i = json.loads(i)
                reg = int(i['reg'])
                _id = int(i['id'])
                data = int(i['value'])
                if i['type'] == 'read':
                    try:
                        if _id == 0:
                            async with self.watt_io as w:
                                data = await w.readWattmeterRegister(reg, 1)
                        else:
                            async with self.evse_io as e:
                                data = await e.readEvseRegister(reg, 1, _id)
                        if data is None:
                            datalayer = {"process": 0, "value": "Error during reading register"}
                        else:
                            datalayer = {"process": 1, "value": int(((data[0]) << 8) | (data[1]))}

                    except Exception as e:
                        datalayer = {"process": e}

                elif i['type'] == 'write':
                    try:
                        if _id == 0:
                            async with self.watt_io as w:
                                data = await w.writeWattmeterRegister(reg, [data])
                        else:
                            async with self.evse_io as e:
                                data = await e.writeEvseRegister(reg, [data], _id)

                        if data is None:
                            datalayer = {"process": 0, "value": "Error during writing register"}
                        else:
                            datalayer = {"process": 1, "value": int(((data[0]) << 8) | (data[1]))}

                    except Exception as e:
                        datalayer = {"process": e}

            yield from picoweb.start_response(resp, "application/json")
            yield from resp.awrite(json.dumps(datalayer))

    def update_data(self, req, resp):
        collect()
        datalayer = {}
        if req.method == "POST":
            req = await self.proccess_msg(req)
            for i in req.form:
                i = json.loads(i)
                if list(i.keys())[0] == 'relay':
                    if self.wattmeter.negotiation_relay():
                        datalayer = {"process": 1}
                    else:
                        datalayer = {"process": 0}
                elif list(i.keys())[0] == 'time':
                    rtc = RTC()
                    rtc.datetime((int(i["time"][2]), int(i["time"][1]), int(i["time"][0]), 0, int(i["time"][3]),
                                  int(i["time"][4]), int(i["time"][5]), 0))
                    self.wattmeter.start_up_time = time()
                    self.wattmeter.time_init = True
                    datalayer = {"process": "OK"}
            yield from picoweb.jsonify(resp, datalayer)

        else:
            yield from picoweb.start_response(resp, "application/json")
            yield from resp.awrite(self.wattmeter.data_layer.__str__())

    def update_evse(self, req, resp):
        yield from picoweb.start_response(resp, "application/json")
        yield from resp.awrite(self.evse.data_layer.__str__())

    def update_wificlient(self, req, resp):

        collect()
        if req.method == "POST":
            datalayer = {}
            size = int(req.headers[b"Content-Length"])
            qs = yield from req.reader.read(size)
            req.qs = qs.decode()
            try:
                i = json.loads(req.qs)
            except:
                pass
            datalayer = await self.wifi_manager.handle_configure(i["ssid"], i["password"])
            self.ip_address = self.wifi_manager.getIp()
            datalayer = {"process": datalayer, "ip": self.ip_address}

            yield from picoweb.start_response(resp, "application/json")
            yield from resp.awrite(json.dumps(datalayer))

        else:
            client = self.wifi_manager.getSSID()
            datalayer = {}
            for i in client:
                if client[i] > -86:
                    datalayer[i] = client[i]
            datalayer["connectSSID"] = self.wifi_manager.getCurrentConnectSSID()
            yield from picoweb.start_response(resp, "application/json")
            yield from resp.awrite(json.dumps(datalayer))

    def update_setting(self, req, resp):
        collect()

        if req.method == "POST":
            datalayer = {}
            req = await self.proccess_msg(req)

            for i in req.form:
                i = json.loads(i)
                datalayer = self.setting.handle_configure(i["variable"], i["value"])
                datalayer = {"process": datalayer}

            yield from picoweb.start_response(resp, "application/json")
            yield from resp.awrite(json.dumps(datalayer))

        else:
            datalayer = self.setting.getConfig()
            yield from picoweb.start_response(resp, "application/json")
            yield from resp.awrite(json.dumps(datalayer))

    def data_table(self, req, resp):
        collect()
        yield from picoweb.start_response(resp)
        yield from self.app.render_template(resp, "datatable.html", (req,))

    def get_esp_id(self, req, resp):
        datalayer = {"ID": " Wattmeter: {}".format(self.setting.getConfig()['ID']), "IP": self.wifi_manager.getIp()}
        yield from picoweb.start_response(resp, "application/json")
        yield from resp.awrite(json.dumps(datalayer))

    def proccess_msg(self, req):
        size = int(req.headers[b"Content-Length"])
        qs = yield from req.reader.read(size)
        req.qs = qs.decode()
        req.parse_qs()
        return req

    async def webServer_run(self):
        try:
            print("Webserver app started")
            self.app.run(debug=False, host='', port=self.port)
            while True:
                await asyncio.sleep(100)
        except Exception as e:
            print("WEBSERVER ERROR: {}. I will reset MCU".format(e))
            reset()
