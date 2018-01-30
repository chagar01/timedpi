# MIT License

# Copyright (c) 2018 Charles Garcia-Tobin

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time
import smbus
import datetime
import inspect
import sys
import RPi.GPIO

DEVICE_ADDRESS = 0x68      #
SMBUS = 3                  #

REG_SECONDS = 0x0      #
REG_MINUTES = 0x1      #
REG_HOURS   = 0x2
REG_DAY     = 0x3      # week day
REG_DATE    = 0x4
REG_MONTH_C = 0x5      # bit 7 is century bits 4 is 10month (months 11 and 12) and bits 3:0 and lower month digit
REG_YEAR    = 0x6

REG_ALARM1_SECONDS  = 0x7      #
REG_ALARM1_MINUTES  = 0x8      #
REG_ALARM1_HOURS    = 0x9
REG_ALARM1_DAY_DATE = 0xA      # week day

REG_ALARM2_MINUTES  = 0xB      #
REG_ALARM2_HOURS    = 0xC
REG_ALARM2_DAY_DATE = 0xD      # week day

REG_CONTROL   = 0xE
REG_STATUS    = 0xF
REG_AG_OFFSET = 0x10
REG_TMP_MSB   = 0x11
REG_TMP_LSB   = 0x12

bus = smbus.SMBus(SMBUS)    


def printCtrlStatus():
    ctr = bus.read_byte_data(DEVICE_ADDRESS, REG_CONTROL)
    sts = bus.read_byte_data(DEVICE_ADDRESS, REG_STATUS)
    print "Control:",hex(ctr)
    print "Status:",hex(sts)
    


def _int2bcd8(n):
    assert n < 100
    x = (n / 10)*16
    x+= n % 10
    return x

def _bcd82int(n):
    assert n < 256
    return 10*(n >> 4)+ (n & 0xF)

def readTime():
    s  = _bcd82int(bus.read_byte_data(DEVICE_ADDRESS, REG_SECONDS))
    mi = _bcd82int(bus.read_byte_data(DEVICE_ADDRESS, REG_MINUTES))
    h  = _bcd82int(bus.read_byte_data(DEVICE_ADDRESS, REG_HOURS))
    wd = bus.read_byte_data(DEVICE_ADDRESS, REG_DAY)
    md = _bcd82int(bus.read_byte_data(DEVICE_ADDRESS, REG_DATE))
    mo = _bcd82int(bus.read_byte_data(DEVICE_ADDRESS, REG_MONTH_C)&0x1F)
    y  = 2000+_bcd82int(bus.read_byte_data(DEVICE_ADDRESS, REG_YEAR))

    d = datetime.datetime(y,mo,md,h,mi,s)

    print d
    return d

def setToSysTime():
    m = datetime.datetime.now()
    # todo stop clock first but in theory should not matter
    bus.write_byte_data(DEVICE_ADDRESS, REG_SECONDS, _int2bcd8(m.second))
    bus.write_byte_data(DEVICE_ADDRESS, REG_MINUTES, _int2bcd8(m.minute))
    bus.write_byte_data(DEVICE_ADDRESS, REG_HOURS, _int2bcd8(m.hour))
    bus.write_byte_data(DEVICE_ADDRESS, REG_DAY, 1+(m.weekday()+1)%7)
    bus.write_byte_datA(DEVICE_ADDRESS, REG_DATE, _int2bcd8(m.day))
    bus.write_byte_data(DEVICE_ADDRESS, REG_MONTH_C, _int2bcd8(m.month))
    bus.write_byte_data(DEVICE_ADDRESS, REG_YEAR, _int2bcd8(m.year % 100))
    readTime()

def wakeIn(s):
    ''' wake again in s seconds'''
    m = datetime.datetime.now()

    # TODO...

    
    # todo stop clock first but in theory should not matter
    bus.write_byte_data(DEVICE_ADDRESS, REG_SECONDS, _int2bcd8(m.second))
    bus.write_byte_data(DEVICE_ADDRESS, REG_MINUTES, _int2bcd8(m.minute))
    bus.write_byte_data(DEVICE_ADDRESS, REG_HOURS, _int2bcd8(m.hour))
    bus.write_byte_data(DEVICE_ADDRESS, REG_DAY, 1+(m.weekday()+1)%7)
    bus.write_byte_data(DEVICE_ADDRESS, REG_DATE, _int2bcd8(m.day))
    bus.write_byte_data(DEVICE_ADDRESS, REG_MONTH_C, _int2bcd8(m.month))
    bus.write_byte_data(DEVICE_ADDRESS, REG_YEAR, _int2bcd8(m.year % 100))
    readTime()

def checkWakeClearAlarm():
    ''' wake again in s seconds'''
    ''' read alarm confug'''
    ctr = bus.read_byte_data(DEVICE_ADDRESS, REG_CONTROL)
    print "Alarm 1 enabled:", (ctr&0x1)!=0
    print "INTCN:", (ctr&0x4)!=0
    sts = bus.read_byte_data(DEVICE_ADDRESS, REG_STATUS)
    A1F =  (sts&0x1)!=0
    print "Alarm 1 A1F:", A1F
    # we expect A1F and a low line either way we reset A1F
    RPi.GPIO.setwarnings(False)
    RPi.GPIO.setmode (RPi.GPIO.BCM)
    RPi.GPIO.setup(3, RPi.GPIO.IN)
    low3 = (RPi.GPIO.input(3) == RPi.GPIO.LOW)
    # clear alarm flag
    sts &= 0xFE # cler LSB 
    bus.write_byte_data(DEVICE_ADDRESS, REG_STATUS, sts)
    print "GPIO 3 was low:", low3
    RPi.GPIO.cleanup()

    
def readAlarm():
    ''' read alarm confug'''
    ctr = bus.read_byte_data(DEVICE_ADDRESS, REG_CONTROL)
    print "Alarm 1 enabled:", (ctr&0x1)!=0
    print "INTCN:", (ctr&0x4)!=0
    sts = bus.read_byte_data(DEVICE_ADDRESS, REG_STATUS)
    print "Alarm 1 A1F:", (sts&0x1)!=0

    ss = bus.read_byte_data(DEVICE_ADDRESS, REG_ALARM1_SECONDS)
    A1M1 = ss >> 7
    ss = ss & 0x7F
    print "Alarm 1 seconds:",_bcd82int(ss)," "

    mm = bus.read_byte_data(DEVICE_ADDRESS, REG_ALARM1_MINUTES)
    A1M2 = mm >> 7
    ss = ss & 0x7F
    print "Alarm 1 minutes:",_bcd82int(mm)

    hh = bus.read_byte_data(DEVICE_ADDRESS, REG_ALARM1_HOURS)
    A1M3 = hh >> 7
    hh = hh & 0x3F
    print "Alarm 1 hours:",_bcd82int(hh)

    dd = bus.read_byte_data(DEVICE_ADDRESS, REG_ALARM1_DAY_DATE)
    A1M4 = dd >> 7
    WD = ((dd>>6)&1)!=0
    dd = dd & 0x3F
    print "Alarm 1 day/date:",_bcd82int(dd)
    print "day is weekday (Sunday == 1):",WD

    if A1M4 > 0:
        if A1M3 > 0:
            if A1M2 > 0:
                if A1M1 > 0:
                    print "Alarm once per second"
                else:
                    print "Alarm when seconds match"
            else:
                print "Alarm when minutes and seconds match"
        else:
             print "Alarm when hours, minutes and seconds match"
    else:
        if WD:
            print "Alarm when week day, hours, minutes and seconds match"
        else:
            print "Alarm when month day, hours, minutes and seconds match"
            
        

def setHHMMAlarm(args):
    ''' '''
    hh = int(args[0])
    mm = int(args[1])

    A1M1 = 0
    A1M2 = 0
    A1M3 = 0
    A1M4 = 0x80
    DYDT = 0


    alarmsec = A1M1 | 0x0
    alarmmin = A1M2 | _int2bcd8(mm)
    alarmhour = A1M3 | _int2bcd8(hh)
    alarmday = A1M4 | DYDT | 0x0

    
    bus.write_byte_data(DEVICE_ADDRESS, REG_ALARM1_SECONDS,alarmsec)
    bus.write_byte_data(DEVICE_ADDRESS, REG_ALARM1_MINUTES,alarmmin)
    bus.write_byte_data(DEVICE_ADDRESS, REG_ALARM1_HOURS,alarmhour)
    bus.write_byte_data(DEVICE_ADDRESS, REG_ALARM1_DAY_DATE,alarmday)
    ctr = bus.read_byte_data(DEVICE_ADDRESS, REG_CONTROL)
    ctr |= 0x1 # bit 0 is A1E
    ctr |= 0x4 # bit 2 is INTCN
    bus.write_byte_data(DEVICE_ADDRESS, REG_CONTROL,ctr)
    sts = bus.read_byte_data(DEVICE_ADDRESS, REG_STATUS)
    sts &= 0xFE # cler LSB 
    bus.write_byte_data(DEVICE_ADDRESS, REG_STATUS, sts)
    readAlarm()
            
    
fset =  [obj for name,obj in inspect.getmembers(sys.modules[__name__])
         if (inspect.isfunction(obj) and name[0]!='_')]

fnames = [obj.__name__ for obj in fset]

def help():
    print "rtc.py command"
    print "\t where command is one of:"
    for fn in fnames:
        print "\t\t",fn
    sys.exit(0)
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        help()
    else:    
        fn = sys.argv[1]
        try:
            ix = fnames.index(fn)
            f = fset[ix]
            if len(sys.argv[2:]):
                f(sys.argv[2:])
            else:
                f()
        except:
            help()
            
            
