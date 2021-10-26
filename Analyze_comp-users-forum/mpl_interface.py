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
    def __init__(self,internal=False):
        self.debug = 0

        self.internal = internal
        print 'mpl_interface.__init__ completed'
        return
    def stackedBarChart(self,y,xlabels,ylabels,title,norm=False):
        '''
        create and fill a stacked bar chart
        returns the title of the bar chart

        inputs:
        y = 2d array, 1 dimensions corresponds to xlabels, other to content for different labels.
        title = global title
        norm = True = Normalize content of each bin to 100%.

        cribbed partly from https://matplotlib.org/1.3.1/examples/pylab_examples/bar_stacked.html
        color map: https://matplotlib.org/1.3.1/examples/color/colormaps_reference.html
        '''

        N = len(xlabels)
        if y.shape[1]!=N :
            print 'mpl_interface.stackedBarChart ERROR len(xlabels)',N,'inconsistent with y.shape[1]',y.shape[1],'title',title
            sys.exit('mpl_interface.stackedBarChart ERROR Input array length mismatch')
        ind = numpy.arange(N)
        width = 0.35

        Nc = y.shape[0]

        #cmap = matplotlib.cm.spectral #2 - 2d most distinct palette
        cmap = matplotlib.cm.Accent  # 1 - this provides the most distinct palette (tested to Nc=11)
        colors = [cmap(k) for k in numpy.linspace(0,1,Nc+1)] 

        denom = numpy.ones(N)
        if norm:
            denom = numpy.zeros(N)
            for i in range(Nc):
                denom += y[i]
            denom = denom
                
        
        p = []
        bottom = numpy.zeros(N)
        for i in range(Nc):
            Y = y[i]/denom
            p.append ( plt.bar(ind, Y, width,  color=colors[i], bottom = bottom) )
            bottom += Y

        f = 1.33
        yma = f*max(bottom)
        #print 'max(bottom)',max(bottom),'yma',yma
        plt.ylim(0.,yma)
        plt.xlim(ind[0]-width/2,ind[-1]+3./2.*width)
        plt.xticks(ind+width/2., xlabels)
        if norm : plt.yticks(numpy.arange(0,f,0.10))
        P = [a[0] for a in p]
        plt.legend( P, ylabels,loc='best',ncol=3, borderaxespad=0., borderpad=.2, handletextpad=0.2, columnspacing=0.4)
#        plt.legend( P, ylabels, bbox_to_anchor=(0., 1.02, 1., .102/5), loc=3, ncol=2+2, mode="expand", borderaxespad=0.)
        Title = title
        if norm: Title += ' (Norm to unity)'
        plt.title(Title)
        plt.grid()
        if self.internal : plt.show()
        
        return Title
            
if __name__ == '__main__' :
    internal = True
    mpli = mpl_interface(internal=internal)

    ntest = 1
    for itest in range(ntest):
        ylabels = ['pony','chicken','dog','duck','goose','penguin','hippo','cat','turkey','kangaroo','wolverine']
        N = len(ylabels)
        ylabels = ['this is a '+q for q in ylabels]
        x = [10., 20., 30., 40., 50.]
        xlabels = [str(a) for a in x]
        Nx= len(x)
        Y = None
        for i in range(N):
            a = numpy.random.randint(1,11,size=Nx)
            if Y is None:
                Y = numpy.array(a)
            else:
                Y = numpy.append(Y,a,axis=0)

        #print 'Y',Y
        Y = numpy.reshape(Y, (N, Nx) )
        #print 'Y',Y
        title = 'this is an example'
        mpli.stackedBarChart(Y,xlabels,ylabels,title,norm=False)
        mpli.stackedBarChart(Y,xlabels,ylabels,title,norm=True)

    listParts = False
    if listParts:
        fn = 'DATA/comp-users-forum_2021-01/107'
        if len(sys.argv)>1 : fn = sys.argv[1]
        mpli.listParts(fn)
        sys.exit('extractMsg listParts ' + fn)

