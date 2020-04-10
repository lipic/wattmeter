import sys
import uio
import uos



class LoggingHandler():
    def __init__(self):
        self.__message =[]
        self.Logging = False
        self.__buffRowLen = 0
        self.count = -1
        self.__loging = False
        #self.enableLogging = 1

    def __iter__(self):
        yield (self.__message) 

    def __next__(self):
        self.count += 1
        if self.count < len(self.__message):
            return self.__message
        else:
            self.count = -1
            raise StopIteration

    def write(self, data):
        if ((self.Logging == True) and data != None):
            if type(data) == bytearray: 
                data = str(data, "ascii")
            
            self.__message.append(data)
            self.__buffRowLen = self.__buffRowLen + 1
            
            if(self.__buffRowLen>10):
                self.__buffRowLen = 0
                self.__message = []
    
    @property
    def eraseMessage(self):
        self.__message = []
         