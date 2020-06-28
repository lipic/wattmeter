import uasyncio as asyncioimport pkg_resourcesimport picowebimport utemplatefrom main import wifiManagerimport jsonclass WebServerApp:          def __init__(self,wlan,wlanStatus,wattmeter,logging,evse):        self.logging = logging        self.wifiManager = wlan        self.ipAddress = self.wifiManager.getIp()        self.wattmeter = wattmeter        self.evse = evse        self.port = 8000        self.ROUTES = [             ("/", self.main),             ("/datatable", self.dataTable),            ("/updateWificlient",self.updateWificlient),             ("/updateSetting",self.updateSetting),            ("/updateData", self.updateData),             ("/settings", self.settings),            ("/getEspID", self.getEspID),            ("/readRegister", self.readRegister)        ]        self.app = picoweb.WebApp(None, self.ROUTES)        def main(self,req, resp):        yield from picoweb.start_response(resp)        yield from self.app.render_template(resp,"main.html")     def settings(self,req, resp):         self.logging.log = False        yield from picoweb.start_response(resp)        yield from self.app.render_template(resp, "settings.html", (req,))            def updateData(self,req, resp):        self.logging.log = True        datalayer = self.wattmeter.dataLayer.data        datalayer.update(self.evse.dataLayer.data)        try:            while 1:                datalayer["log"] = self.logging.__next__()        except StopIteration:            pass        self.logging.eraseMessage        yield from picoweb.jsonify(resp,datalayer)                def updateWificlient(self,req, resp):        self.logging.log = False        if req.method == "POST":            datalayer = {}                       size = int(req.headers[b"Content-Length"])            qs = yield from req.reader.read(size)            req.qs = qs.decode()            req.parse_qs()            for i in req.form:                 i = json.loads(i)                 print(i["ssid"],i["password"])                   datalayer = self.wifiManager.handle_configure(i["ssid"],i["password"])                self.ipAddress=self.wifiManager.getIp()                datalayer = {"process":datalayer,"ip":self.ipAddress}                        print("datalayer: ",datalayer)                yield from picoweb.jsonify(resp,datalayer)                        else:            datalayer = self.wifiManager.getSSID()            yield from picoweb.jsonify(resp,datalayer)                def readRegister(self,req, resp):        self.logging.log = False        if req.method == "POST":            datalayer = {}                       size = int(req.headers[b"Content-Length"])            qs = yield from req.reader.read(size)            req.qs = qs.decode()            req.parse_qs()            for i in req.form:                 i = json.loads(i)                 register = int(i["register"])                data = await self.wattmeter.readWattmeterRegister(register,1)                datalayer = {"data":data}                        yield from picoweb.jsonify(resp,datalayer)                                #Funkce pro vycitani a ukladani nastaveni    def updateSetting(self,req, resp):        from main import __config__        setting = __config__.Config()                if req.method == "POST":            datalayer = {}                        size = int(req.headers[b"Content-Length"])            qs = yield from req.reader.read(size)            req.qs = qs.decode()            req.parse_qs()            for i in req.form:                 i = json.loads(i)                 datalayer = setting.handle_configure(i["variable"],i["value"])                datalayer = {"process":datalayer}                        yield from picoweb.jsonify(resp,datalayer)                        else:            datalayer = setting.getConfig()            yield from picoweb.jsonify(resp,datalayer)                                def dataTable(self,req, resp):        yield from picoweb.start_response(resp)        yield from self.app.render_template(resp, "datatable.html", (req,))    def getEspID(self,req,resp):            print("ID : ESP1, IP : ",self.wifiManager.getIp())            datalayer = {"ID":"ESP1", "IP":self.wifiManager.getIp()}            yield from picoweb.jsonify(resp,datalayer)                  async def webServerRun(self, delay):        while True:            print("Start webserver App")            self.app.run(debug=True, host=self.ipAddress,port=self.port)             await asyncio.sleep(delay)