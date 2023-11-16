#!/usr/bin/env python
'''
lifetime of lambda c from cascade c

20220222
'''
import sys,os
import matplotlib.pyplot as plt
import numpy
import math


class PtoG():
    def __init__(self):
        print('PtoG.__init__ Completed')
        return
    def readXVIII(self,fn='data.txt'):
        '''
        load in contents of table XVIII
        '''
        f = open(fn,'r')
        Table = {}
        Map   = {}
        for line in f:
            key = None
            if line[0]=='#':
                continue
            elif 'p∗(D∗)' in line:
                for i,s in enumerate(line.split()):
                    if i==0:
                        key = s
                        Table[key] = []
                        Map[key] = key
                    else:
                        Table[key].append(s)
            else:
                for i,s in enumerate(line.split()):
                    if i==0:
                        key = s
                        Table[key] = []
                        if 'N' in key and 'γ' in key:  Map['Ng'] = key
                        elif 'ε' in key and 'γ' in key: Map['eg'] = key
                        elif 'N' in key and 'π0' in key: Map['Npi0'] = key
                        elif 'ε' in key and 'π0' in key: Map['epi0'] = key
                        else: Map[key] = key
                            
                    else:
                        v,u = float(s.split('±')[0]),float(s.split('±')[1])
                        Table[key].append( [v,u] )

        f.close()
        print('PtoG.readXVIII Table',Table,'\nMap',Map)
        return Table,Map
    def main(self):
        Table,Map = self.readXVIII()
        # calculate ratios. Ratio = Npi0/Ng x eg/epi0
        key = Map['Npi0']
        for i,Npi0 in enumerate(Table[key]):
            epi0 = Table[Map['epi0']][i]
            eg   = Table[Map['eg']][i]
            Ng   = Table[Map['Ng']][i]
            r = Npi0[0]/Ng[0] * eg[0]/epi0[0]
            dr= r*math.sqrt( math.pow(Npi0[1]/Npi0[0],2) +math.pow(Ng[1]/Ng[0],2) +math.pow(epi0[1]/epi0[0],2) +math.pow(eg[1]/eg[0],2)) 
            print('PtoG.main Ratio',Table['Ratio'][i],'Calculated {0:.3f} {1:.4f}'.format(r,dr))
        
        return
    
if __name__ == '__main__' :
    L = PtoG()
    L.main()

