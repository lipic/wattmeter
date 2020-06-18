import struct
import socket
import uselect as select
from main import modbus
from main import wattmeter

import uasyncio as asyncio

class Server:
    
    def __init__(self, wattmeter):
        self.tcpModbus = tcpModbus(wattmeter)

        
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
            await asyncio.sleep(1)

    async def run_client(self, sock, cid):

        self.socks.append(sock)
        sreader = asyncio.StreamReader(sock)
        swriter = asyncio.StreamWriter(sock, {})

        print('Got connection from client', cid)
        try:
            while True:
                
                res = sock.recv(50)#sreader.read(12)
                
                if res == b'':
                    raise OSError
                
                #proccess modbus msg
                try:
                    print("Received Data: ",res)
                    result = await self.tcpModbus.modbusCheckProccess(res)
                    print("Sended Data: ",result)
                    await swriter.awrite(result)  # Echo back
                    await asyncio.sleep_ms(500)
            
                except Exception as e:
                    print(e)

        except OSError:
            pass
        print('Client {} disconnect.'.format(cid))
        sock.close()
        self.socks.remove(sock)




class tcpModbus(modbus.Modbus, wattmeter.Wattmeter):
    
    def __init__(self,wattmeter):
        self.wattmeter = wattmeter
        modbus.Modbus.__init__(self)
        
        
    async def __evse_readData(self,reg,length):
        readRegs = self.read_regs(reg, length)
        self.uart.write(readRegs)
        await asyncio.sleep(0.1)
        receiveData = self.uart.read()
    
    async def modbusCheckProccess(self, receiveData):
        ID        = receiveData[6]
        FCE     = receiveData[7]
        if(len(receiveData) < 12):
            raise "Err: data miss"
        
        if((FCE != 3) and (FCE != 16)):
            raise "Err: bad function"
        
        if((ID != 1) and (ID != 2)):
            raise "Err: bad id"
    
        if(ID == 1):
            return await self.proccessWattmeterData(receiveData)
                
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
                values.append(int((receiveData[12+i]<<8) | receiveData[13+i]))
            data = await self.wattmeter.writeWattmeterRegister(reg,values)
            sendData = bytearray(receiveData[:7])
            if((data != "Error") and (data !="Null")):
                sendData += data
               
            sendData += bytearray([0]) 
            sendData += bytearray([numb])


        return sendData

