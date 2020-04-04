import sys
import uio
import uos



class LoggingHandler(uio.IOBase):
    def __init__(self):
        self.data = ''
        self.pos = 0

    def write(self, data):
        self.data += (data.decode("ascii"))


    def readinto(self):
        return None