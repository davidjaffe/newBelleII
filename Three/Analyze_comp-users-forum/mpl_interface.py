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
import random


class mpl_interface():
    def __init__(self,internal=False):
        self.debug = 0

        self.internal = internal

        Nc = 25
        self.rcolors = []
        CM = matplotlib.cm
        for cmap in [CM.Accent, CM.Dark2, CM.Paired, CM.Pastel1]:
            self.rcolors.extend( [cmap(k) for k in numpy.linspace(0,1,Nc+1)] )

        print('mpl_interface.__init__ completed')
        return
    def histo(self,Y,xlo,xhi,nbin=None,dx=None,xlabel=None,ylabel=None,title=None,grid=False):
        '''
        create and fill a histogram with range xlo,xhi and plotted xlo,xhi
        if dx is None, then hist has nbin bins
        if nbin is None, then hist has nbin = (xhi-xlo)/dx bins
        '''
        if nbin is None:
            if dx is None: dx = 1.
            nbin = int((xhi-xlo)/dx)
        hist,edges = numpy.histogram(Y,bins=nbin,range=(xlo,xhi))
        w = edges[1]-edges[0]

        plt.bar(edges[:-1],hist,width=w)
        ylo,yhi = 0.,max(hist)*1.05
        plt.xlim(xlo,xhi)
        plt.ylim(ylo,yhi)
        if grid : plt.grid()
        if xlabel is not None: plt.xlabel(xlabel)
        if ylabel is not None: plt.ylabel(ylabel)
        if title is not None: plt.title(title)
        if self.internal : plt.show()
        return title
    def plot2d(self,x,y,z,xlabels=None,ylabels=None,title=None,colorbar=True):
        '''
        create and fill a 2d plot 
        optionally add a color bar
        z = z(ny,nx) with shape (Nrows,Ncolumns) = bin contents
        x = shape (Ncolums+1) = bin edges
        y = shape (Nrows+1) = bin edges
        '''

        plt.pcolor(x,y,z)
        if xlabels is not None : plt.xticks( (x[1:]+x[:-1])/2., xlabels, rotation=45,ha='right')
        if ylabels is not None : plt.yticks( (y[1:]+y[:-1])/2., ylabels)
        if title is not None   : plt.title(title)
        if colorbar : plt.colorbar()
        plt.tight_layout()
        if self.internal : plt.show()
        return title
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
            print('mpl_interface.stackedBarChart ERROR len(xlabels)',N,'inconsistent with y.shape[1]',y.shape[1],'title',title)
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
    def nicePallet(self,n):
        '''
        return distinctive list of colors of length n
        '''
        colors = []
        N = len(self.rcolors)
        for i,A in enumerate(self.rcolors):
            if i%(N/n)==0 and len(colors)<n : colors.append( A )
        for i in range(1):
            c1,c2 = colors[:n/2],colors[n/2:]
            colors = [val for pair in zip(c1,c2) for val in pair]
        return colors
    def pie(self,x,labels,title=None):
        '''
        plot pie chart
        with title positioned to avoid wedge labels
        and distinctive wedge colors
        '''
        Nc = len(x)
        colors = self.nicePallet(Nc)
        plt.pie(x,labels=labels,colors=colors,labeldistance=1.05)
        if title is not None : plt.title( title, loc='left', bbox={'pad':5, 'facecolor':'none'} )
        if self.internal : plt.show()
        return title
        

           
if __name__ == '__main__' :
    internal = True
    mpli = mpl_interface(internal=internal)

    testPie = True
    if testPie :
        for N in [25, 35, 45, 55, 101]:

            k = [random.randint(1,30) for x in range(N)]
            l =  [str(x) for x in k]
            x,labels = k,l
            title = 'this is the title. it is a very long title. \nand it cannot be used on this experiment because it extends too far'
            TT = mpli.pie(x,labels,title=title)
    
    testHisto = False
    if testHisto :
        y = list(range(2,33))
        y.extend(list(range(1,3)))
        for x in range(15,24):
            y.extend(list(range(7,x)))
        for x in range(8,15):
            y.extend(list(range(3,x)))
        Y = numpy.array(y)
        xlo,xhi = 0.,50.
        dx = 1.0
        nbin = int((xhi-xlo)/dx)
        mpli.histo(Y,xlo,xhi,nbin=25,title='25 bins',grid=True)
        for dx in [1.0, 0.5]:
            mpli.histo(Y,xlo,xhi,dx=dx,title='bin size is '+str(dx))

    testPlot2d = False
    if testPlot2d :
        nr = 5+3
        nc = nr
        x = numpy.arange(nc+1)
        y = numpy.arange(nr+1)
        z = []
        for ir in range(nr):
            for ic in range(nc):
                if ic==ir :
                    z.append( numpy.random.random()*100. )
                else:
                    z.append( numpy.random.random()*10. )
        Z = numpy.reshape(numpy.array(z),(nc,nr))
        xlabels = ['this is a '+q for q in  ['cow','horse','goat','pig','cat','dog','rat','awk']]
        ylabels = xlabels

        #print 'x,y,Z',x,y,z
        
        mpli.plot2d(x,y,Z,xlabels=xlabels,ylabels=ylabels,title='Down at the farm')
        sys.exit('end testPlot2d')
    
    ntest = 0 
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

