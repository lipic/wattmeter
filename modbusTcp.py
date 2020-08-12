import struct
import socket
import uselect as select
import modbus
from main import wattmeter
from main import __config__
from main import evse
import asyn
import uasyncio as asyncio

class Server:
    
    def __init__(self,lock):
        self.tcpModbus = tcpModbus()
        self.lock = lock

    async def run(self, loop, port=8123):
        addr = socket.getaddrinfo('', port, 0, socket.SOCK_STREAM)[0][-1]
        print(addr)
        s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # server socket
        s_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
            await asyncio.sleep_ms(100)

    async def run_client(self, sock, cid):

        self.socks.append(sock)
        sreader = asyncio.StreamReader(sock)
        swriter = asyncio.StreamWriter(sock, {})

        print('Got connection from client', cid)
        try:
            while True:
                res = await sreader.read(6)
                try:
                    res += await sreader.read(length)
                except Exception as e: 
                    print(e)
                if res == b'':
                    raise OSError
                #proccess modbus msg
                try:
                    print("Received Data: ",res)
                    await self.lock.acquire()
                    result = await self.tcpModbus.modbusCheckProccess(res)
                    print("Sended Data: ",result)
                    await swriter.awrite(result) 
                    self.lock.release()
                except Exception as e:
                    self.lock.release()
                    print(e)

        except OSError:
            pass
        print('Client {} disconnect.'.format(cid))
        sock.close()
        self.socks.remove(sock)




class tcpModbus():
    
    def __init__(self):
        self.wattmeter = wattmeter.Wattmeter(lock = asyn.Lock(), ID=1,timeout=50,baudrate =9600,rxPin=26,txPin=27)
        self.evse = evse.Evse(baudrate = 9600, wattmeter = self.wattmeter, lock = asyn.Lock())
        self.config = __config__.Config()
            
    async def modbusCheckProccess(self, receiveData):
        a = (receiveData[0]<<8)|receiveData[1]
        b = (receiveData[2]<<8)|receiveData[3]
        c = (receiveData[4]<<8)|receiveData[5]
        ID = receiveData[6]
        FCE = receiveData[7]
        
        print("Transaction Identifier: {}, Protocol Identifier: {}, Message Length: {}, ID: {}, Function: {}".format(a,b,c,ID,FCE))

        if(len(receiveData) < 12):
            raise Exception("Error: data miss")
        
        if((FCE != 3) and (FCE != 16)):
            raise Exception("Error: bad function")
        
        if((ID > 0) and (ID<100)):
            return await self.proccessEvseData(receiveData)    
        
        if(ID == 100):
            return await self.proccessWattmeterData(receiveData)
        
        if(ID == 101):
            return await self.proccessEspData(receiveData)    
            
    async def proccessWattmeterData(self,receiveData):
        data = bytearray()
        length = 0
        #modbus function 0x03
        if(receiveData[7] == 3):
            reg = int((receiveData[8]<<8) | receiveData[9])
            length = int((receiveData[10]<<8) | receiveData[11])
            data = await self.wattmeter.readWattmeterRegister(reg,length)
            sendData = bytearray(receiveData[:8])
            sendData += bytearray([length * 2])
            if((data != "Error") and (data !="Null")):
                sendData += data
            
        
        if(receiveData[7] == 16):
            reg = int((receiveData[8]<<8) | receiveData[9])
            numb = int((receiveData[10]<<8) | receiveData[11])
            values = []
            
            for i in range(0,numb):
                values.append(int(receiveData[13+(2*i)] | receiveData[14+(2*i)]))
                
            data = await self.wattmeter.writeWattmeterRegister(reg,values)
            sendData = bytearray(receiveData[:8])
            if((data != "Error") and (data !="Null")):
                sendData += data
            sendData += bytearray([0])
            sendData += bytearray([numb])

        return sendData
    
    async def proccessEspData(self,receiveData):
        length = 0
        data = bytearray()
        FCE = receiveData[7]
    
        #modbus function 0x03
        if(FCE == 3):
            reg = int((receiveData[8]<<8) | receiveData[9])
            length = int((receiveData[10]<<8) | receiveData[11])
            sendData = bytearray(receiveData[:8])
            sendData += bytearray([length * 2])
            espData = self.config.getConfig()
            ESP_REGISTER_LEN =  len(espData)
            START_REGISTER = 1000
        
            if(reg> (ESP_REGISTER_LEN + START_REGISTER)):
                raise Exception("Error, bad number of reading register")
            if((reg+length)>(ESP_REGISTER_LEN + START_REGISTER)):
                raise Exception("Error, bad length of reading register")
            
            newESPReg = {}
            for i in espData:
                newESPReg[START_REGISTER] = espData[i]
                START_REGISTER = START_REGISTER + 1
                
            cnt = 0
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
            sendData += data
                    
        if(FCE == 16):
            reg = int((receiveData[8]<<8) | receiveData[9])
            length = int((receiveData[10]<<8) | receiveData[11])
            
            espData = self.config.getConfig()
            ESP_REGISTER_LEN =  len(espData)
            START_REGISTER = 1000
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

            sendData = bytearray(receiveData[:10])
            sendData += bytearray([0])
            sendData += bytearray([length])

        return sendData
              
    async def proccessEvseData(self,receiveData):
        data = bytearray()
        length = 0
        ID = receiveData[6]
        #modbus function 0x03
        if(receiveData[7] == 3):
            reg = int((receiveData[8]<<8) | receiveData[9])
            length = int((receiveData[10]<<8) | receiveData[11])
            data = await self.evse.readEvseRegister(reg,length,ID)
            sendData = bytearray(receiveData[:8])
            sendData += bytearray([length * 2])
            if((data != "Error") and (data !="Null")):
                sendData += data
            
        
        if(receiveData[7] == 16):
            reg = int((receiveData[8]<<8) | receiveData[9])
            numb = int((receiveData[10]<<8) | receiveData[11])
            values = []
            for i in range(0,numb):
                values.append(int(receiveData[13+(2*i)] | receiveData[14+(2*i)]))

            data = await self.evse.writeEvseRegister(reg,values,ID)
            sendData = bytearray(receiveData[:8])
            if((data != "Error") and (data !="Null")):
                sendData += data
            sendData += bytearray([0])
            sendData += bytearray([numb])

        return sendData