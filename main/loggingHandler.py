import sys
import uio
import uos



class LoggingHandler(uio.IOBase):
    def __init__(self):
        self.data =""
        self.enableLogging = False
        self.buffRowLen = 0

    def write(self, data):
        if (self.enableLogging == True):
            if type(data) == bytearray: 
                data = str(data, "ascii")
                self.data += data
            else:
                self.data += data
            self.data +="\n"
            self.buffRowLen = self.buffRowLen + 1
            if(self.buffRowLen>10):
                self.buffRowLen = 0
                self.data = ""
    
