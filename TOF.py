#!/usr/bin/env python
'''
simple TOF calculations, adapted from ONETON/cerenkov.py 
units: particle energy in MeV, pathlenght in cm, wavelength in nm, optical photon energy in nm

20190113
'''
import sys
import math
import ParticleProperties
import numpy


class TOF():
    def __init__(self):
        self.hc = 1239.841930 # nm per eV
        self.cerconst = 369.907 # cerenkov OP/eV/cm. Eqn 30.43 RPP2012
        self.pp  = ParticleProperties.ParticleProperties() # for masses
        self.velc = 299792458. * 1.e2 * 1.e-9 # metres per second * 1.e2 (cm/m) * 1.e-9 (s/ns) = cm/ns
        return
    def getBeta(self,KE,particle):
        m = self.pp.getMass(particle)
        T = max(0.,KE)
        return math.sqrt(T*(T+2*m))/(m+T)
    def getTOF(self,L,KE,particle):
        v = self.getBeta(KE,particle)*self.velc
        tof = -1.
        if v>0: tof = L/v
        return tof
    def writeTable(self):
        '''
        table of p,E,L,TOF, delta_TOF
        '''
        L = 125. + 25. # cm (inner radius of endcap KLM is 1253 mm), assume 25cm is average interaction point
        for particle in ['K0L','mu+']:
            m = self.pp.getMass(particle)
            KE = 1.e6
            tof_b1 = self.getTOF(L,KE,particle) # TOF for beta=1
            print '{0:>10} {1:>10} {2:>10} {3:>10} {4:>10} {5:10}'.format('p(MeV/c)','E(MeV)','L(cm)','TOF(ns)','dTOF(ns)',particle)
            for KE in [100., 200., 300., 400., 500., 750., 1000., 2000.]:
                E = KE + m
                beta = self.getBeta(KE,particle)
                p = beta * E
                tof = self.getTOF(L,KE,particle)
                print '{0:10.1f} {1:10.1f} {2:10.1f} {3:10.1f} {4:10.1f}'.format(p,E,L,tof,tof-tof_b1)
        return
        
if __name__ == '__main__':
    tof = TOF()
    tof.writeTable()
