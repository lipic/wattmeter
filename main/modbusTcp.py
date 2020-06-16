import struct
import socket
import uselect as select
from main import modbus
from main import wattmeter

import uasyncio as asyncio

class Server:
    
    def __init__(self):
        self.tcpModbus = tcpModbus(ID=1,timeout=50,baudrate =9600,rxPin=26,txPin=27)

        
    async def run(self, loop, port=8123):
        addr = socket.getaddrinfo('', port, 0, socket.SOCK_STREAM)[0][-1]
        print(addr)
        s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # server socket
#         s_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
                #self.run_client(c_sock, client_id)
                loop.create_task(self.run_client(c_sock, client_id))
                client_id += 1
            await asyncio.sleep_ms(200)

    async def run_client(self, sock, cid):

        self.socks.append(sock)
        sreader = asyncio.StreamReader(sock)
        swriter = asyncio.StreamWriter(sock, {})

        print('Got connection from client', cid)
        try:
            while True:
                res =await sreader.read(12)
                if res == b'':
                    raise OSError
                
                #proccess modbus msg
                print("Coming data: ",res)
                result = await self.tcpModbus.modbusCheckProccess(res)
                print("Result: ",result)
                await swriter.awrite(result)  # Echo back
               # await swriter.drain()



        except OSError:
            pass
        print('Client {} disconnect.'.format(cid))
        sock.close()
        self.socks.remove(sock)

class tcpModbus(modbus.Modbus, wattmeter.Wattmeter):
    
    def __init__(self,ID, timeout, baudrate , rxPin, txPin):
        wattmeter.Wattmeter.__init__(self,ID, timeout, baudrate , rxPin, txPin)
        modbus.Modbus.__init__(self)
        
    async def __wattmeter_readData(self,reg,length):
        readRegs = self.read_regs(reg, length)
        self.uart.write(readRegs)
        await asyncio.sleep(0.1)
        receiveData = self.uart.read()
        try:
            if (receiveData and  (0 == self.modbusClient.mbrtu_data_processing(receiveData))):
                data = []
                for i in range(length):
                    data.append(receiveData[i+3])
                return data
            else:
                return "Null"
        except:
            return "Error"
        
    async def __evse_readData(self,reg,length):
        readRegs = self.read_regs(reg, length)
        self.uart.write(readRegs)
        await asyncio.sleep(0.1)
        receiveData = self.uart.read()
    
    async def modbusCheckProccess(self, receiveData):
        ID        = receiveData[6]
        FCE     = receiveData[7]
        if(len(receiveData) < 2):
            print("Err: data miss")
        
        if((FCE != 3) and (FCE != 16)):
            print("Err: bad function")
        
        if((ID != 1) and (ID != 2)):
            print("Err: bad function")
    
        if(ID == 1):
            return await self.proccessWattmeterData(receiveData)
                
    def proccessWattmeterData(self,receiveData):
        data = b''
        length = 0
        if(receiveData[7] == 3):
            reg = int((receiveData[8]<<8) | receiveData[9])
            length = int((receiveData[10]<<8) | receiveData[11])
            data = await self.__wattmeter_readData(reg,length)

        sendData = bytearray(receiveData[:8])
        sendData.append(length * 2)
        #sendData.append(5)
        if((data != "Error") and (data !="Null")):
            sendData.append(data)
        
        return sendData

