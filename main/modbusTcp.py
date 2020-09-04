import socket
import uselect as select
from main import __config__
import  evseComInterface
import  wattmeterComInterface
import asyn 
import uasyncio as asyncio
 
class Server:
    
    def __init__(self,wattmeterInterface,evseInterface):
        self.tcpModbus = tcpModbus(wattmeterInterface,evseInterface)

    async def run(self, loop, port=8123):
        addr = socket.getaddrinfo('', port, 0, socket.SOCK_STREAM)[0][-1]
        print("Tcp Modbus client listen on port:{} and addr: {}".format(port,addr))
        s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM,socket.IPPROTO_TCP)  # server socket
        s_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 10)
        s_sock.bind(addr) 
        s_sock.listen(5)
        self.socks = [s_sock]  # List of current sockets for .close()
        print('Awaiting connection on port', port)
        poller = select.poll()
        poller.register(s_sock, select.POLLIN)
        client_id = 1  # For user feedback
        while True:
            res = poller.poll(1)  # 1ms block
            if res:  # Only s_sock is polled
                c_sock, addr = s_sock.accept()  # get client socket
                loop.create_task(self.run_client(c_sock, client_id))
                client_id += 1
            await asyncio.sleep_ms(20)

    async def run_client(self, sock, cid):

        self.socks.append(sock)
        sreader = asyncio.StreamReader(sock)
        swriter = asyncio.StreamWriter(sock, {})

        print('Got connection from client', cid)
        try:
            while True:
                res = await sreader.read(6)
                try:
                    length = int((res[4]<<8) | res[5])
                    res += await sreader.read(length)
                except Exception as e: 
                    print(e)
                if res == b'':
                    raise OSError
                #proccess modbus msg
                try:
                    print("Received Data: ",res)
                    result = await self.tcpModbus.modbusCheckProccess(res)
                    print("Sended Data: ",result)
                    await swriter.awrite(result)
                except Exception as e:
                    print("run_client exception: {}".format(e))

        except OSError:
            pass
        print('Client {} disconnect.'.format(cid))
        sock.close()
        self.socks.remove(sock)

class tcpModbus():
    
    def __init__(self,wattmeterInterface,evseInterface):
        self.wattmeter = wattmeterInterface
        self.evse = evseInterface
        self.config = __config__.Config()
            
    async def modbusCheckProccess(self, receiveData):
        if(len(receiveData) < 12):
            raise Exception("Error: data miss")
        try:
            ID = receiveData[6]
            FCE = receiveData[7]
            LEN = int((receiveData[10]<<8) | receiveData[11])
            REG = int((receiveData[8]<<8) | receiveData[9])
        
            if((FCE != 3) and (FCE != 16)):
                raise Exception("Error: Unsuported MODBUS function")
            
            UD = bytearray()
            if((ID > 0) and (ID<100)):
                UD = await self.proccessEvseData(FCE,LEN,REG,ID)    
        
            if(ID == 100):
                UD = await self.proccessWattmeterData(FCE,LEN,REG)
        
            if(ID == 101):
                UD = await self.proccessEspData(FCE,LEN,REG)    
            
            sendData = bytearray(receiveData[:8])
            sendData[4]=0
            if(FCE == 3):
                sendData[5]=(LEN*2)+3
                sendData += bytearray([LEN * 2])
                if(UD!="Null"):
                    sendData+= UD
                else:
                    sendData[5] = 0
            elif(FCE == 16):
                sendData[5]==6
                if(UD!="Null"):
                    sendData+= UD
                else:
                    sendData[5] = 0
                sendData += bytearray([0])
                sendData += bytearray([LEN])
            return sendData
        except Exception as e:
            print("ModbusTCp ",e)
            return b''
    async def proccessWattmeterData(self,fce,length,reg,ID=1):
        #modbus function 0x03
        if(fce == 3):
            return await self.wattmeter.readWattmeterRegister(reg,length)
        
        if(fce == 16):
            values = []
            for i in range(0,length):
                values.append(int(receiveData[13+(2*i)] | receiveData[14+(2*i)]))
            return await self.wattmeter.writeWattmeterRegister(reg,values)

    
    async def proccessEspData(self,fce,length,reg,ID=1):
        espData = self.config.getConfig()
        ESP_REGISTER_LEN =  len(espData)
        START_REGISTER = 1000
        #modbus function 0x03
        if(fce == 3):
            if(reg> (ESP_REGISTER_LEN + START_REGISTER)):
                raise Exception("Error, bad number of reading register")
            if((reg+length)>(ESP_REGISTER_LEN + START_REGISTER)):
                raise Exception("Error, bad length of reading register")
            
            newESPReg = {}
            for i in espData:
                newESPReg[START_REGISTER] = espData[i]
                START_REGISTER = START_REGISTER + 1
                
            cnt = 0
            data = bytearray()
            for i in range(reg,(reg+length)):
                if(cnt<length):
                    cnt = cnt + 1
                    if(((newESPReg[i]) == 'True') or ((newESPReg[i]) == 'False') ):
                        value = int(newESPReg[i])
                        data += bytearray([((value>>8) & 0xff)])
                        data += bytearray([(value) & 0xff])
                    else:
                        hodnota = int(newESPReg[i].replace(".",""))
                        data += bytearray([((hodnota>>8) & 0xff)])
                        data += bytearray([(hodnota) & 0xff])
                else:
                    break
            return data
                    
        if(fce == 16):
            if(reg> (ESP_REGISTER_LEN + START_REGISTER)):
                raise Exception("Error, bad number of reading register")
            if((reg+length)>(ESP_REGISTER_LEN + START_REGISTER)):
                raise Exception("Error, bad length of reading register")
            
            newESPReg = {}
            for i in espData:
                newESPReg[START_REGISTER] = espData[i]
                START_REGISTER = START_REGISTER + 1
                
            values = []
            for i in range(0,length*2):
                values.append(receiveData[13+i])

            cnt = 0
            for i in range(reg,(reg+length)): 
                if(cnt<length):
                    listData = list(espData)
                    self.config.handle_configure(variable=listData[reg-1000+cnt],value=int((values[cnt*2]<<8) | values[(cnt*2)+1]))
                    cnt = cnt + 1
                else:
                    break
            return bytearray(reg)

    async def proccessEvseData(self,fce,length,reg,ID=1):

        #modbus function 0x03
        if(fce == 3):
            return await self.evse.readEvseRegister(reg,length,ID)
        
        if(fce == 16):
            values = []
            for i in range(0,length):
                values.append(int(receiveData[13+(2*i)] | receiveData[14+(2*i)]))
            return await self.evse.writeEvseRegister(reg,values,ID)
