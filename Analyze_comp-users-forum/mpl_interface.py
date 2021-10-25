#!/usr/bin/env python
'''
interface to matplotlib

make stacked bar charts

20211025
'''
#import math
import sys,os
import glob
import email, base64
import numpy
import matplotlib
import matplotlib.pyplot as plt


class mpl_interface():
    def __init__(self):
        self.debug = 0

        print 'mpl_interface.__init__ completed'
        return
    def stackedBarChart(self,x,y,xlabels,ylabels,title):
        '''
        create and fill a stacked bar chart
        inputs
        x = 1d array
        y = 2d array, 1 dimensions corresponds to x, other to content for different labels.

        cribbed partly from https://matplotlib.org/1.3.1/examples/pylab_examples/bar_stacked.html
        color map: https://matplotlib.org/1.3.1/examples/color/colormaps_reference.html
        '''

        N = len(x)
        if y.shape[1]!=N :
            print 'mpl_interface.stackedBarChart ERROR len(x)',N,'inconsistent with y.shape[1]',y.shape[1],'title',title
            sys.exit('mpl_interface.stackedBarChart ERROR Input array length mismatch')
        ind = numpy.arange(N)
        width = 0.35

        Nc = y.shape[0]
        colors = [matplotlib.cm.hsv(k) for k in numpy.linspace(0,1,Nc)]

        p = []
        bottom = numpy.zeros(N)
        for i in range(Nc):
            Y = y[i]
            #print 'mpl_interface.stackedBarChart i',i,'ind',ind,'Y',Y
            p.append ( plt.bar(ind, Y, width,  color=colors[i], bottom = bottom) )
            bottom += Y

        yma = 1.35*max(bottom)
        plt.ylim(0.,yma)
        plt.xlim(ind[0]-width/2,ind[-1]+3./2.*width)
        plt.xticks(ind+width/2., xlabels)
        P = [a[0] for a in p]
        plt.legend( P, ylabels,loc='best',ncol=2, borderaxespad=0., borderpad=.2)
#        plt.legend( P, ylabels, bbox_to_anchor=(0., 1.02, 1., .102/5), loc=3, ncol=2+2, mode="expand", borderaxespad=0.)
        plt.title(title)

        plt.show()
        
        return 
            
if __name__ == '__main__' :
    mpli = mpl_interface()

    ntest = 5
    for itest in range(ntest):
        N = 7
        ylabels = ['pony','chicken','dog','duck','goose','penguin','hippo']
        ylabels = ['this is a '+q for q in ylabels]
        x = [10., 20., 30., 40., 50.]
        xlabels = [str(a) for a in x]
        Nx= len(x)
        X = numpy.array( x )
        Y = None
        for i in range(N):
            a = numpy.random.randint(1,11,size=Nx)
            if Y is None:
                Y = numpy.array(a)
            else:
                Y = numpy.append(Y,a,axis=0)
        #print 'X',X
        #print 'Y',Y
        Y = numpy.reshape(Y, (N, Nx) )
        #print 'Y',Y
        title = 'this is an example'
        mpli.stackedBarChart(X,Y,xlabels,ylabels,title)

    listParts = False
    if listParts:
        fn = 'DATA/comp-users-forum_2021-01/107'
        if len(sys.argv)>1 : fn = sys.argv[1]
        mpli.listParts(fn)
        sys.exit('extractMsg listParts ' + fn)

