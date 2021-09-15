#!/usr/bin/env python
'''
plot stuff
20210915
'''
import sys
import math

import numpy
import matplotlib.pyplot as plt

class plotter():
    def __init__(self):
        return
    def iTOPspe(self,x,params=[7.89,1.086,2.255,4333]):
        '''
        function from page 15 of TOPWeeklyMeeting201015Kojima.pdf
        '''
        p0,p1,p2,x0 = params
        f = p0*math.power(x/x0,p1)*math.exp(-math.power(x/x0,p2))
        return f
    def plot1(self):
        x = numpy.linspace(0,20000.)
        plt.plot(x,self.iTOPspe(x),'-')
        plt.show()
        return
        
if __name__ == '__main__':
    plot = plotter()
    plot.plot1()
