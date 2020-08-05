#!/usr/bin/env python
'''
parse B2MMS list 
20200305
'''
#import math
import sys,os
import csv
import institute

#import datetime


class member():
    def __init__(self,validCountry=None,inputFile=None):

        print 'member.__init__ validCountry',validCountry,'inputFile',inputFile
        
        self.debug = 0

        self.USA = 'U.S.A.'

        self.validCountry = self.USA
        if validCountry is not None: self.validCountry = validCountry
        self.csvfn = 'B2MMS_US_active_members_20200305.csv'
        if inputFile is not None: self.csvfn = inputFile
        self.latexfile = 'Membership_table.tex'
        self.IRfile    = 'Collaboration_board.tex'

        self.INSTITUTE = institute.institute()
        
        return
    def rdr(self):
        '''
        read in csv file
return dict[institution] = [ [firstname,lastname,category,country], [], ...]
        '''
        validStatus = 'Active'
        validCountry= self.validCountry # 'U.S.A.'

        statusFails,countryFails = 0,0
        
        f = open(self.csvfn,'r')
        rdr = csv.reader(f)
        header = rdr.next()
        print 'member.rdr validCountry',validCountry,'Opened',self.csvfn
        if self.debug > 0 : print 'member.rdr First row',header
        colwords = ['Given Name', 'Family Name','Membership Category',\
                        'Belle2 Institution', 'Status', 'Country','IR']
        colabr   = ['firstn','lastn','cat','inst','status','country','IR']
        colidx = {}
        for w,a in zip(colwords,colabr):
            colidx[a] = header.index(w)
        mem = {}
        reps= {}
        for row in rdr:
            inst   = row[colidx['inst']]
            firstn = row[colidx['firstn']]
            lastn  = row[colidx['lastn']]
            cat    = self.fixCategory( row[colidx['cat']] )
            status = row[colidx['status']]
            country= row[colidx['country']]
            IR     = row[colidx['IR']]

            if (validCountry.lower()=='all' or country==validCountry) and status==validStatus : 
                
                if inst not in mem:
                    mem[inst] = [ [firstn,lastn,cat,country] ]
                else:
                    mem[inst].append( [firstn,lastn,cat,country] )

                if 'Yes' in IR:
                    reps[inst] = [firstn,lastn,inst] 
                    
            if validCountry.lower()!='all' and country != validCountry:
                countryFails += 1
            if status != validStatus:
                statusFails +=1
        

        f.close()
        tot = 0
        totUSA = 0
        totgs= 0 # total grad students (PhD and MSc)
        Countrys = []
        print ' {0:>7} {1}'.format('Members','Institution')
        for inst in sorted(mem):
            tot += len(mem[inst])
            print '{0:>7d} {1}'.format(len(mem[inst]),inst.replace('"',''))

            country = mem[inst][0][3]
            if country==self.USA : totUSA += len(mem[inst])
            if country not in Countrys : Countrys.append(country)

            for member in mem[inst] :
                if member[2]=='MSc student' or member[2]=='PhD student': totgs += 1
        USAfrac = -1.
        if tot>0: USAfrac = float(totUSA)/float(tot)
        print 'Total',tot,'members (',totgs,'grad students) at',len(mem),'institutions in',len(Countrys),'countrys'
        print 'USA total {0} members, {1:.2f}% of Total members'.format(totUSA,100.*USAfrac)
        print 'Total of',statusFails,'with invalid status and',countryFails,'with invalid country'

        # print reps
        
        return mem, reps
    def fixCategory(self,cat):
        '''
        return modified category
        '''
        newcat = cat
        if cat == 'Physicist - faculty/staff' : newcat = 'Faculty/Staff'
        if cat == 'Physicist - term limited'  : newcat = 'Postdoc'
        return newcat
    def main(self):
        mem, reps = self.rdr()
        institutions,INST = self.INSTITUTE.rdr()
        if self.validCountry == 'U.S.A.':
            self.writelatex(mem,INST)
            self.writeInstReps(reps,INST)
        return
    def writeInstReps(self,reps,INST):
        ''''
        write latex table of long institute names and IR reps for USA
        '''
        with open(self.IRfile,'w') as f:
            f.write('\\begin{enumerate}\n')
                        
            for sname in sorted(reps):
                lname = INST[sname.replace('"','')]
                lname = self.fixLongname(lname)
                IR = reps[sname]
                firstn,lastn = IR[:2]
                line = '\\item '+lname+':'+' '+firstn+' '+ lastn + '\n'
                f.write(line)
            f.write('\\end{enumerate}\n')
        f.close()
        print 'member.writeInstReps Wrote',self.IRfile

        return
    def fixLongname(self,lname):
        '''
        some fixes to long names of institutions
        '''
        fixed = lname
        for bogus in ['(UM)','(CMU)', '(Virginia Tech)']:
            if bogus in lname : fixed = lname.replace(bogus,'')
        return fixed
        
    def writelatex(self,mem,INST):
        '''
        write nested itemized lists of institutions and members
        given names and membership categories

        presently lists members by category for each institution, but members are not alphabetized by last name
        '''

        with open(self.latexfile,'w') as f:
            f.write('\\begin{itemize}\n')
            for inst in sorted(mem):
                lname = INST[inst.replace('"','')]
                lname = self.fixLongname(lname)
#                f.write('\\item '+inst.replace('"','')+'\n\\begin{itemize}\n')
                f.write('\\item '+lname+'\n\\begin{itemize}\n')
                oldcat = None
                line = ''
                for e in sorted( mem[inst], key=lambda x:x[2]) :
                    firstn,lastn,cat,cty = e
                    if cat!=oldcat:
                        oldcat = cat
                        f.write(line[:-1]+'\n')
                        line = '\\item '+cat+': '
                    line += ' ' + firstn + ' ' + lastn + ','
                    #f.write('\\item '+firstn+' '+lastn+', '+cat+'\n')
                if len(line)>0: f.write(line[:-1]+'\n')
                f.write('\\end{itemize}\n')
            f.write('\\end{itemize}\n')
        f.close()
        print 'member.writelatex Wrote',self.latexfile

if __name__ == '__main__' :

    validCountry = 'U.S.A.'
    inputFile = None
    if len(sys.argv)>1 :
        validCountry = sys.argv[1]
    if len(sys.argv)>2 :
        inputFile = sys.argv[2]
    m = member(validCountry,inputFile)
    m.main()
    
