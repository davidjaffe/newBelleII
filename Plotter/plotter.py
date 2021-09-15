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
        x = numpy.linspace(0,20000.)
        
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
if __name__ == '__main__':
    plot = plotter()
    plot.plot1()
