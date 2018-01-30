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
import datetime
import inspect
import sys
import re
import fileinput

h = ''' simple cron style format with 
# is commment
linespecs of format:
d   h   m cmd [args...]
Where:
cmd is a full command line, any parameters behind that are 
passed on to the command

d/h/m are day hour minute. 

Minutes as special and are in 10s, Valid values are 0-5, for a job 
triggering off the 0th, 10th, 20th, and so on up to 50th minute

h are in the range 0-23
d are in range 0-6 where 0 is Monday

d/m/h may be single integers as per above, or one of the following:

* -- indicate every possible value e.g. to trigger a job every day at
     10 am the spec would be:

     * 10 0 cmd

a-b  range a to b, a doesnt have to be lower than b, wrapping works. 
     e.g. to trigger a job every day at 10 am, except saturday and sunday 
     do:
     0-4 10 0 cmd '''


class timeSpec:
    @staticmethod
    def parseSpecElem(ss,limit):
        # matching *
        if ss == '*':
            return range(0,limit+1)
        
        # matching a - b
        m = re.match('(\d+)\s*-\s*(\d+)',ss)
        if m:
            a = int(m.group(1))
            b = int(m.group(2))
            if a > limit or b > limit:
                return None
            if a < b:
                return range(a,b+1)
            else:
                return range(0,b+1)+range(a,limit+1)
            
        # matching single digit
        m = re.match('\d+',ss)
        if m:
            a = int(m.group(0))
            if a > limit:
                return None
            return [a]

        return None
        

    def __init__(self,ss):
        # first ensure it matches basic format
        m = re.match('\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+.*)',ss)
        if m == None:
            raise Exception('bad format: '+ss)
        ds = m.group(1)
        hs = m.group(2)
        ms = m.group(3)
        self.cmd = m.group(4)
        self.d = timeSpec.parseSpecElem(ds,6)
        if not self.d:
            raise Exception('bad format: '+ss)
        self.h = timeSpec.parseSpecElem(hs,23)
        if not self.h:
            raise Exception('bad format: '+ss)
        self.m = [x*10 for x in timeSpec.parseSpecElem(ms,5)]
        if not self.m:
            raise Exception('bad format: '+ss)

        self.stimes = list()
        for d in sorted(self.d):
            for h in sorted(self.h):
                for m in sorted(self.m):
                    self.stimes.append(m*60+h*3600+d*24*3600)


    def next(self):
        ''' number of seconds to next event'''
        # this ignores daylight savings right now
        n = datetime.datetime.now()
        ns = n.second+n.minute*60+n.hour*3600+n.weekday()*24*3600
        print "!!",ns
        # find times that are higher than ns (which is now in seconds so far in the week)
        lns = [x for x in self.stimes if x >= ns]
        print "!!",lns
        if len(lns) > 0:
            return lns[0]-ns
        else:
            # if there are none, then find earliest event next week
            return 7*24*3600+self.stimes[0]-ns

    def __repr__(self):
        ds = str(self.d)
        hs = str(self.h)
        ms = str(self.m)
        ss = str(self.stimes)
        return "d:"+ds+"\n"+"h:"+hs+"\n"+"m:"+ms+"\n"+"stimes:"+ss+"\ncmd:"+self.cmd
    
   
    __str__ = __repr__    
        

class TimeSpecs:
    def __init__(self,fname):
        self.specs = list()
        for line in fileinput.input(fname):
            line=line.strip()
            if not len(line) or line[0]=='#':
                continue
            try:
                self.specs.append(timeSpec(line))
            except:
                pass
                
    def next():
        nl = [s.next() for s in self.specs]
        return min(nl)

    def __repr__(self):
        for s in self.specs:
            print s
   
    __str__ = __repr__    


def test():
    tests = ['fffii',
             '* * *',
             '* * * pepe',
             '1-2 5 1-2 foo',
             '0 5 1 foo',
             '6-0 5 1-2 foo']
    
    for t in tests:
        print "Trying ",t
        try:
            ts = timeSpec(t)
            print ts
            print ">>",ts.next()
        except:
            continue


def ftest(ffs):
    for f in ffs:
        import pdb; pdb.set_trace()
        TS = TimeSpecs(f)
        print TS
        
fset =  [obj for name,obj in inspect.getmembers(sys.modules[__name__])
         if (inspect.isfunction(obj) and name[0]!='_')]

fnames = [obj.__name__ for obj in fset]


def help():
    print h
    print "scron.py command"
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
