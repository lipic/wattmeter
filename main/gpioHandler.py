from machine import Pin
import uasyncio as asyncio

class GpioHandler:
    #        self.ledAPI = ledHandler.LedHandler({'obj':{'obj1':{'task':"LED_RUN", 'config':{'pin':23},'action':{'repeateTime':10}},
       #                                                                                  'obj2':{'task':"LED_ERR", 'config':{'pin':21},'action':{'repeateTime':10}}}})
    def __init__(self,obj):
        self.ledObj= {}
        if type(obj) is dict:
            self.ledObj = obj
                 
                
    def objControll(self,timer,obj):
        if (('config' in obj.keys()) and ('action' in obj.keys())):
            if ('Ontime' in obj['action'].keys() and ('Offtime' in obj['action'].keys())):
                    
                if((obj['action']['Ontime'] == 0)and (obj['action']['Offtime'] == 0)):
                    if 'state' in obj['action'].keys():
                        if (obj['action']['state'] == 'ON'):
                            Pin(obj['config']['pin'], Pin.OUT).on()
                        else:
                            Pin(obj['config']['pin'], Pin.OUT).off()

                
                #opakovani
                else:
                    if((obj['action']['repeat'])>= obj['action']['repeatCnt']):
                        #On time    
                        if((obj['action']['Ontime']) > obj['action']['timeCnt']):
                            Pin(obj['config']['pin'], Pin.OUT).on()
                        #Off time
                        elif((obj['action']['Offtime']) > obj['action']['timeCnt']):
                            Pin(obj['config']['pin'], Pin.OUT).off()
                        obj['action']['timeCnt'] += 1
                        #reset Time cnt
                        if(obj['action']['timeCnt'] >= (obj['action']['Offtime'])):
                            if(obj['action']['repeat'] != 0):
                                obj['action']['repeatCnt'] += 1
                            obj['action']['timeCnt'] = 0
                    else:
                        Pin(obj['config']['pin'], Pin.OUT).off()
                        obj['action']['timeCnt'] = 0
                        obj['action']['DeltaCnt'] += 1
                        if(obj['action']['DeltaCnt']>= obj['action']['Delta']):
                            obj['action']['repeatCnt'] = 0
                            obj['action']['DeltaCnt'] = 0
            else:
                print("Please set all need parameters")
            
    def callback(self,task,type,process=None,value=None):
        if((task in self.ledObj)and(type in self.ledObj[task])):
            self.ledObj[task][type][process] = value
        else:
            print("Key error")

    def getStatus(self,task,type,process=None,value=None):
        if((task in self.ledObj)and(type in self.ledObj[task])):
            if(process != None):
                if(value != None):
                    return  self.ledObj[task][type][process][value]
                else:
                    return  self.ledObj[task][type][process]
            else:
                return  self.ledObj[task][type]
        else:
            print("Key error")
    async def ledHandlerObj(self):
        timer = 0
        while True:
            timer += 1
            for fce in self.ledObj:
                self.objControll(timer,self.ledObj[fce])
            if(timer>=100):
                timer=0
            await asyncio.sleep(0.1)