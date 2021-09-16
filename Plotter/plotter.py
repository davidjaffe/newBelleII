#!/usr/bin/env python
'''
plot stuff
20210915
'''
import sys
import math

import numpy
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

class plotter():
    def __init__(self):
        self.params=[7.89,1.086,2.255,4333.]
        self.maxADC = 20000.
        return
    def iTOPspe(self,x):
        '''
        function from page 15 of TOPWeeklyMeeting201015Kojima.pdf
        '''
        p0,p1,p2,x0 = self.params

        f = p0*pow(x/x0,p1)*numpy.exp(-pow(x/x0,p2))
        return f
    def plot1(self):
        '''
        compare function used for spe with gaussian
        '''
        x = numpy.linspace(1.,self.maxADC,num=int(self.maxADC))
        
        y = self.iTOPspe(x)
        plt.plot(x,y,'-')

        yint = numpy.sum(y)*(x[1]-x[0])
        ymax = max(y)
        imax = numpy.argmax(y)
        mu = x[imax]
        sg = 2000.
        y = yint*mlab.normpdf(x,mu,sg)
        plt.plot(x,y,'x',color='green')

        #plt.yscale('log')
        plt.grid()
        plt.show()
        return
    def plot2(self):
        '''
        claim by Kojima 20191022 b2gm_top_monitor_muroyama.pdf
        is Gain = integral( x*f(x) dx ) / integral( f(x) dx )
        where f(x) = iTOPspe function, x = ADC charge
        Actually the eqn above just defines the <x> = expectation value of x. 

        also estimate threshold in ADC charge from Kojima's 20201015 p15 where he defines efficiency = integral_threshold( f(x) dx ) / integral( f(x) dx ) and shows an efficiency of 0.996. 

        '''
        x = numpy.linspace(0.,self.maxADC,num=int(self.maxADC))
        y = self.iTOPspe(x)
        up = numpy.sum(x*y)
        dn = numpy.sum(y)
        Gain = -1.
        if dn>0. : Gain = up/dn
        print 'plotter.plot2 up,dn,Gain=',up,dn,Gain
        #
        # threshold estimate
        effgoal = 0.996
        for i,u in enumerate(x):
            q = numpy.sum(y[i:])
            eff = q/dn
            if eff < effgoal:
                effm1 = numpy.sum(y[i-1:])
                m = (eff-effm1)/(u-x[i-1])
                b = (effm1*u - eff*x[i-1])/(u-x[i-1])
                thres = (effgoal - b)/m
                print 'plotter.plot2 eff[x],x',eff,u,'effgoal,thres=',effgoal,thres
                break
            
        
        return
if __name__ == '__main__':
    plot = plotter()
    plot.plot2()
