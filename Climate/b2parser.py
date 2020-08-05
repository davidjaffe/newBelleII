#!/usr/bin/env python
'''
parse htm files extracted from belle ii webpages
20191017
'''
import math
import sys,os

import datetime
#import numpy
#import copy

import re
import glob # used in __init__

#from lxml.html import parse  # used by readB2GM
#from lxml import etree

#import matplotlib.pyplot as plt

class b2parser():
    def __init__(self):

        self.debug = 1

        files = glob.glob("CDATA/Shift*.htm")
        files.sort()
        self.B2shiftfiles = files
        print 'b2parser.__init__ will process the following shift files '
        for a in self.B2shiftfiles: print a
        print '\n'
        self.lastFileIndex = -1
            
        
        return
    def getNextShiftFile(self):
        '''
        return name of the next shift file or None if there is no next file
        '''
        self.lastFileIndex += 1
        if self.lastFileIndex < len(self.B2shiftfiles):
            return self.B2shiftfiles[ self.lastFileIndex ]
        return None
    def readShift(self,fn,debug=0):
        '''
        use empirical method of parsing htm file with shifter information
        Extract string between 'Mail address' and 'return', clean the string and then append a string with date information,
        render the resulting string to get the email, institution, collaborator name and date

        returns dict shiftInfo[email] 
        shiftInfo[email] = [ inst, name, contiguous_shift_ranges]
        where contiguous_shift_ranges = [ [firstday1,lastday1], [firstday2,lastday2], ...]

        '''
        if debug>0: print 'b2parser.readShift -------------------------> Process',fn
        fnl = fn.split('.')
        fntemp = fnl[0].replace(' ','') + '.temporary'
        os.system("grep -E 'book_month|Mail address|workday|holiday' " + fn + " > " + fntemp)

        
        Shifters = []
        Date,Month = None,None
        self.rfmt = rfmt = '%d %a %B %Y'  # as read from input file
        self.wfmt = wfmt = '%Y-%m-%d'     # as written to output list Shifters

        f = open(fntemp,'r')
        for line in f:
            if debug>2: print line[:-1]
            if 'book_month' in line:
                i = line.find('book_month')
                i1= i + line[i:].find('>')
                i2= i1+ line[i1:].find('<')
                Month = line[i1+1:i2]
                if debug>1: print 'Month',Month
            elif ('workday' in line or 'holiday' in line) and 'shift_' not in line:
                i = line.find('workday')
                if i<0: i = line.find('holiday')
                i += len('holiday')
                newDate = line[i:i+12].replace("'>","").replace('\n','').replace('\t','')
                if 0:
                    j = line.find('Weekly')
                    if j>0 :
                        i = j + len('Weekly')
                        k = i + line[i:].find('<')
                        newDate = line[i:k]
                if len(newDate)>0 : Date = 'date:' + newDate
                if debug>1: print 'Date',Date
            elif 'Mail address' in line:
                i = line.find('Mail address')
                j = i + line[i:].find('return')
                if debug>1: print 'i,j',i,j
                if debug>1: print 'preclean s',line[i:j]
                s = self.clean(line[i:j])
                if debug>1: print 'postclean s',s
                u = s + Date
                info = self.render(u)
                dobj = info[-1] + ' ' + Month
                info[-1] = datetime.datetime.strptime(dobj,rfmt).strftime(wfmt) 
                Shifters.append( info )
                if debug>0: print 'b2parser.readShift','%s' % ', '.join(map(str,info))
            else:
                pass
        f.close()
        print 'b2parser.readShift Processed ================> Data on',len(Shifters),' shifts from',fntemp,'made from',fn
        if os.path.isfile(fntemp):
            os.remove(fntemp)
        else:
            print 'b2parser.readShift WARNING Failed to delete temporary file',fntemp
        shiftInfo = self.compressor(Shifters)
        return shiftInfo
    def compressor(self,Shifters,debug=0):
        '''
        produce dict of per-person contiguous shifts given list of day-by-day shift information
        item in Shifters is [email, inst, name, date] with date=  'yyyy-mm-dd'
        temporary dicts :
        shiftID[email] =  [inst, name]
        shiftDates[email] = [date1, date2, date3 ..., daten] 
        output dict :
        shiftInfo[email] = [ inst, name, contiguous_shift_ranges]
        where contiguous_shift_ranges = [ [firstday1,lastday1], [firstday2,lastday2], ...]
        '''
        
        shiftID = {}
        shiftDates = {}
        for shift in Shifters:
            email,inst,name,date = shift
            if email not in shiftID:
                shiftID[email] = [inst,name]
                shiftDates[email] = [date]
            else:
                shiftDates[email].append(date)
                if shiftID[email][0]!=inst or shiftID[email][1]!=name:
                    print 'b2parser.compressor ERROR Original inst/name',shiftID[email][0]+'/'+shiftID[email][1],'does not match',inst+'/'+name
                    sys.exit('b2parser.compressor ERROR This should not happen')

        shiftInfo = {}
        for email in sorted(shiftID):
            inst,name = shiftID[email]
            days = shiftDates[email]
            contig = self.daterange(days)
            if debug>1: print email,inst,'%s' % ', '.join(map(str,days)),contig
            if debug>0: print email,inst,contig
            shiftInfo[email] = [inst, name, contig]
        
        return shiftInfo
    def daterange(self,dates):
        '''
        given list of dates, produce list of contiguous dates
        '''
        debug = 0
        
        fmt = self.wfmt
        contig = None
        if debug>0: print 'b2parser.daterange fmt,dates',fmt,dates
        for d in dates:
            if contig is None:
                contig = [ [d,d] ]
            else:
                d2 = contig[-1][-1]
                if debug>0 : print 'b2parser.daterange contig',contig,'d',d,'d2',d2
                dt2= datetime.datetime.strptime(d2,fmt)  
                dt = datetime.datetime.strptime(d,fmt)
                if dt==dt2+datetime.timedelta(days=1):
                    contig[-1][-1] = d   # extend current range
                else:
                    contig.append([d,d]) # start new range
        return contig
    def clean(self,dirty):
        crud = ["',STICKY, CAPTION,'","', WIDTH,250);",
                    '&lt', '&gt',
                    'br;', 'b;', ';br', ';/;',';;;',
                    ';/b', ';b ',
                    '</b>', '<br>', '</b>', '<b>', '  ', ';  ;',
                    'brbrb', '/bbr',
                    '" onmouseout="', '" onmouseout="']
        clean = ' '
        x = dirty
        for dirt in crud: x = x.replace(dirt,clean)
        return x
    def render(self,line):
        '''
        given line extracted from shift.htm file, return email address, institution short name, collaborator name, date
        date may be missing
        '''
        show = False
        
        ma = 'Mail address:'
        i1 = line.find(ma)+len(ma)
        line[i1:]
        fi = 'First Institution:'
        i2 = line.find(fi)
        email = line[i1:i2].strip()
        email = email.replace(';','').strip()
        
        i2 += len(fi)
        i3 = line[i2:].lstrip().find(' ')
        for special in ['Roma Tre','HEPHY Vienna']:
            if special in line[i2:]:
                i3 = len(special)
                #print 'b2parser.render special',special,'line[:-1]',line[:-1],'line[i2:].lstrip()[:i3]',line[i2:].lstrip()[:i3]
                #show = True
                    
        inst = line[i2:].lstrip()[:i3]
        inst = inst.replace(';','').strip()
        dt = 'date:'
        i4 = line.find(dt)
        if i4>0:
            date = line[i4+len(dt):]
            cname= line[i2:i4].replace(inst,'').replace(';','').strip()
        else:
            date = None
            cname= line[i2:].replace(inst,'').strip()

        if show: print 'b2parser.render result',[email,inst,cname,date]
        return [email, inst, cname, date]
    def mainShift(self):
        '''
        main steering file for getting shifter info
        '''
        for fn in self.B2shiftfiles:
            self.readShift(fn)
        return
if __name__ == '__main__' :
   
    bp = b2parser()
    bp.mainShift()
