
## Values must be in byte
class Modbus:
    table = (
    0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241,
    0xC601, 0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440,
    0xCC01, 0x0CC0, 0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40,
    0x0A00, 0xCAC1, 0xCB81, 0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841,
    0xD801, 0x18C0, 0x1980, 0xD941, 0x1B00, 0xDBC1, 0xDA81, 0x1A40,
    0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01, 0x1DC0, 0x1C80, 0xDC41,
    0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0, 0x1680, 0xD641,
    0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081, 0x1040,
    0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
    0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441,
    0x3C00, 0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41,
    0xFA01, 0x3AC0, 0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840,
    0x2800, 0xE8C1, 0xE981, 0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41,
    0xEE01, 0x2EC0, 0x2F80, 0xEF41, 0x2D00, 0xEDC1, 0xEC81, 0x2C40,
    0xE401, 0x24C0, 0x2580, 0xE541, 0x2700, 0xE7C1, 0xE681, 0x2640,
    0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0, 0x2080, 0xE041,
    0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281, 0x6240,
    0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
    0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41,
    0xAA01, 0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840,
    0x7800, 0xB8C1, 0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41,
    0xBE01, 0x7EC0, 0x7F80, 0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40,
    0xB401, 0x74C0, 0x7580, 0xB541, 0x7700, 0xB7C1, 0xB681, 0x7640,
    0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101, 0x71C0, 0x7080, 0xB041,
    0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0, 0x5280, 0x9241,
    0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440,
    0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
    0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841,
    0x8801, 0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40,
    0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41,
    0x4400, 0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641,
    0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040 )

    def __init__(self):
        self.INITIAL_MODBUS = 0xFFFF
        self.SLAVE_ADDRESS = 1
        self.value = []
        self.count = 0
        self.address = 0
        self.func = 0
        
    def calcString(self,st, crc):
       
        """Given a bunary string and starting CRC, Calc a final CRC-16 """
        for ch in st:
            crc = (crc >> 8) ^ self.table[(crc ^ ord(ch)) & 0xff]
        return crc
    
    def write_regs (self,address, values):
    
        self.address = address
        self.func = 16
        self.value = values 
    
        if((self.SLAVE_ADDRESS < 0) or (self.SLAVE_ADDRESS >255)):
            print("error: Bad Unit Id or Slave Address")
            return inDct
         
        MODBUS_buffer_tx = None
        request1 = None
        result = None
        add1 = (self.address >> 8) & 0xFF
        add2 = self.address & 0xFF
       
        if(self.func in [16]):
            MODBUS_buffer_tx = [(chr)(self.SLAVE_ADDRESS),(chr)(self.func&0xff),(chr)(add1&0xff),(chr)(add2&0xff),(chr)(0),(chr)(len(self.value)),(chr)(2*len(self.value))]
            
            for i in range(len(self.value)):
                MODBUS_buffer_tx.append((chr) ((self.value[i] >> 8)&0xff))
                MODBUS_buffer_tx.append((chr) (self.value[i]&0xff))
        
        else:
            print({"error: Unsupported Function"})
     
        
        # at this point we have the basic Modbus message
        if(MODBUS_buffer_tx):
              
            crc16 = self.calcString(MODBUS_buffer_tx, self.INITIAL_MODBUS)
            high_crc = (int)(crc16>>8)
            low_crc =  (int)(crc16&0xff)
            request1 = [(self.SLAVE_ADDRESS),(self.func),(add1),(add2),(0),(len(self.value)),(2*len(self.value))]
            for i in range(len(self.value)):
                request1.append((int) ((self.value[i] >> 8) & 0xff))
                request1.append((int) ((self.value[i] >> 0) & 0xff))
            request1.append(low_crc)
            request1.append(high_crc)
            result = self.int_to_byte(request1)


        return result
      
        
        

    def read_regs (self,address,count):
        self.func = 3
        self.address = address
        self.count = count
        if((self.SLAVE_ADDRESS < 0) or (self.SLAVE_ADDRESS >255)):
            print("error: Bad Unit Id or Slave Address")
            return inDct
        
        MODBUS_buffer_tx = None
        request1 = None
        result = None
     
        add1 = (self.address >> 8) & 0xff
        add2 = self.address & 0xff
    
        if(self.func in [1,2,3,4]):
    
            MODBUS_buffer_tx = [(chr)(self.SLAVE_ADDRESS),(chr)(self.func),(chr)(add1),(chr)(add2),(chr)(0),(chr)(self.count)]
       
        else:
            print({"error: Unsupported Function"})
        
        # at this point we have the basic Modbus message
        if(MODBUS_buffer_tx):
            crc16 = self.calcString(MODBUS_buffer_tx, self.INITIAL_MODBUS)
            high_crc = (int)(crc16>>8)
            low_crc =  (int)(crc16&0xff)
            request1 = [self.SLAVE_ADDRESS,self.func,add1,add2,0,self.count,low_crc,high_crc]
            result = self.int_to_byte(request1)
        
        return result
    

 
    def int_to_byte (self,integ):
        
        st= bytearray(len(integ))
        for i in range(len(integ)):
            x = integ[i]
            st[i] =  x
       
        return st


    
    # Problem, when use TCP232 you must use (8,len(byte)), TCP232 E2 only len(byte) 
    def byte_to_int (self,byte):
       
        if(isinstance(byte, list)):
            print("Convert list to byte array")
            byte = self.list_to_byte(byte)
        
        data = []
        for i in range(len(byte)): 
            x = int(byte[i])           
            data.append(x)
            
        return data  
        
    def list_to_byte (self,byte):
        byt = (str)(byte)
        b = bytearray()
        b.extend(map(ord, byt))
        print(b)
  
        return b    


    def mbrtu_data_processing(self,received_message): 
       
        regsCnt = 0
        values = []
        Modbus_for_crc=''
        self.MODBUS_buffer_rx = self.byte_to_int (received_message)
    
        
        if (len(self.MODBUS_buffer_rx) > 6):
            #response 01
            if (self.MODBUS_buffer_rx[0] == self.SLAVE_ADDRESS):
                #response 03
                if (self.MODBUS_buffer_rx[1] == 3):
                    regsCnt = self.MODBUS_buffer_rx[2]
                    
                    for i in (range( 3 + regsCnt )):
                        Modbus_for_crc += (chr)(self.MODBUS_buffer_rx[i])
    
                    crc16 = self.calcString(Modbus_for_crc, self.INITIAL_MODBUS)
                    high_crc = (int)((crc16>>8)&0xff)
                    low_crc =  (int)(crc16&0xff)
                
                
                    # check CRC bytes
                    if (low_crc != self.MODBUS_buffer_rx[3 + (regsCnt )]):
                        raise Exception("mbrtu_data_processing: bad low CRC code")
                    if (high_crc != self.MODBUS_buffer_rx[4 + (regsCnt )]):
                        raise Exception("mbrtu_data_processing: bad high CRC code")
                    
                return 0
                 
                
            #response 16
                if (self.MODBUS_buffer_rx[1] == 16):
                    Modbus_for_crc16=''
                    for i in (range(6)):
                        Modbus_for_crc16 += (chr)(self.MODBUS_buffer_rx[i])
                    
                    crc16 = self.calcString(Modbus_for_crc16, self.INITIAL_MODBUS)
                    high_crc = (int)(crc16>>8)
                    low_crc =  (int)(crc16&0xff)
                           
                    # check CRC bytes
                    if (low_crc != self.MODBUS_buffer_rx[6]):
                        raise Exception("mbrtu_data_processing: bad low CRC code")
                    if (high_crc != self.MODBUS_buffer_rx[7]):
                        raise Exception("mbrtu_data_processing: bad high CRC code")
                    addres = (0xff00 & (self.MODBUS_buffer_rx[2] << 8)) + (0xff & self.MODBUS_buffer_rx[3])
                    numWritten = self.MODBUS_buffer_rx[5]
                    #print(numWritten," registers were written to start address: ",addres)
                    
                    return 1  
            else:
                raise Exception("mbrtu_data_processing: wrong slave address")
        else:
            raise Exception("mbrtu_data_processing: receive buffer too short")