from machine import Pin
import uasyncio as asyncio

class ErrorHandler:
       
    def __init__(self):
        self.ledErr  = Pin(21, Pin.OUT)
        self.__errType = 0
        self.REPEAT_CNT = 0
        self.OnTIME =1#100mS
        self.OffTIME = 3#300mS
        self.TimeCNT =0
        self.DELTA = 40
        self.DELTA_CNT = 0
    
    def addError(self,numb):
        self.__errType |= numb
        
    def removeError(self,numb):
        self.__errType &= ~numb

        
    async def ledErrorHandler(self):
        while True:
            if((self.__errType-1) >= self.REPEAT_CNT):
                self.TimeCNT += 1
                if(self.OnTIME >= self.TimeCNT):
                    self.ledErr.on()
                elif(self.OffTIME >= self.TimeCNT):
                    self.ledErr.off()
                else:
                    self.TimeCNT=0
                    self.REPEAT_CNT +=1
            else:
                self.ledErr.off()
                self.DELTA_CNT += 1
                if(self.DELTA <= self.DELTA_CNT):
                    self.REPEAT_CNT = 0
                    self.DELTA_CNT = 0
                    self.TimeCNT=0 
            await asyncio.sleep_ms(100)       