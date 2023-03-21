#!/usr/bin/env python
'''
parse B2MMS list to list institutions
20200421
'''
#import math
import sys,os
import csv

#import datetime


class institute():
    def __init__(self):

        self.debug = 0

        self.csvfn = '/Users/djaffe/Documents/Belle II/IB/Membership/Institutions/institutes_20230321.csv' 
#        self.csvfn = '/Users/djaffe/Documents/Belle II/IB/Membership/Institutions/institutes_20200421.csv' #'B2MMS_US_active_members_20200305.csv'
        self.textfile = 'Institute_list.txt'
        self.columnfile = 'Institute_column.txt'
        
        return
    def rdr(self):
        '''
        read in csv file, return list of institution full names

        '''
        f = open(self.csvfn,'r')
        rdr = csv.reader(f)
        header = rdr.next()
        print 'institute.rdr Opened',self.csvfn
        if self.debug > 0 : print 'member.rdr First row',header
        colwords = ['Institution Short Name/Consortium','Institution Full Name','Address Line 1',\
                        'Address Line 2','Country','City','Postal Code','Link','Department','IR',\
                        'Consortium members','Region','Show members']
        colabr   = ['shortn','fulln','add1','add2','country','city','code','link','dept','IR','Consort','region','ShowM']
        colidx = {}
        for w,a in zip(colwords,colabr):
            colidx[a] = header.index(w)
        institutions = []
        INST = {}
        for row in rdr:
            inst   = row[colidx['fulln']]
            shortn = row[colidx['shortn']]
            inst = self.fixInst(inst,shortn)
            institutions.append(inst)
            INST[shortn] = inst
        

        f.close()
        print 'institute.rdr Found',len(institutions),'institutions in',self.csvfn
        return institutions,INST
    def fixInst(self,input,shortn):
        '''
        return modified institute name
        '''
        output = input.replace('Univ.','University')
        if input=='Institute of physics, Vietnam academy of science and technology (VAST) , Hanoi, Viet Nam':
            output = 'Institute of physics Vietnam Academy of Science and Technology'
        if shortn=='IHEP-Russia' :
            output = 'Institute for High Energy Physics Protvino'
        return output
    def main(self):
        institutions,INST = self.rdr()
        S = ''  # long string
        C = ''  # column
        for inst in institutions:
            last = (inst == institutions[-1])
            if last : S += 'and '
            S += inst
            C += inst + ' \n'
            if not last : S += ', '
            if last : S += ' \n'
        f = open(self.textfile,'w')
        f.write(S)
        f.close()
        print 'institute.main',len(institutions),'institutions Wrote',self.textfile
        f = open(self.columnfile,'w')
        f.write(C)
        f.close()
        print 'institute.main Wrote',self.columnfile
        return


if __name__ == '__main__' :

    m = institute()
    m.main()
    
