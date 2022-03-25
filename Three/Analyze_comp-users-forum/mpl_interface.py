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
import datetime, calendar

class mpl_interface():
    def __init__(self,internal=False):
        self.debug = 0

        self.internal = internal

        Nc = 17
        self.rcolors = []
        CM = matplotlib.cm
        for cmap in [CM.Accent, CM.Dark2, CM.Paired, CM.Pastel1, CM.Set1, CM.Set2, CM.Set3]:
            self.rcolors.extend( [cmap(k) for k in numpy.linspace(0,1,Nc+1)] )

        print('mpl_interface.__init__ completed')
        return
    def histo(self,Y,xlo,xhi,nbin=None,dx=None,xlabel=None,ylabel=None,title=None,grid=False,logy='liny'):
        '''
        create and fill a histogram with range xlo,xhi and plotted xlo,xhi
        if dx is None, then hist has nbin bins
        if nbin is None, then hist has nbin = (xhi-xlo)/dx bins
        '''
        #print('mpl_interface.histo Inputs xlo,xhi,nbin,dx,xlabel,ylabel,title',xlo,xhi,nbin,dx,xlabel,ylabel,title)
        if nbin is None:
            if dx is None: dx = 1.
            nbin = int((xhi-xlo)/dx)
        hist,edges = numpy.histogram(Y,bins=nbin,range=(xlo,xhi))
        w = edges[1]-edges[0]
        #print('mpl_interface.histo edges[0],edges[1],edges[-1]',edges[0],edges[1],edges[-1],'w,nbin,dx',w,nbin,dx,'hist[0],hist[1],hist[2],hist[-1]',hist[0],hist[1],hist[2],hist[-1])

        plt.bar(edges[:-1],hist,width=w, edgecolor='red',align='edge')
        if grid : plt.grid()
        if logy.lower()=='logy' :
            plt.yscale('log')
        else:
            ylo,yhi = 0.,max(hist)*1.05
            plt.xlim(xlo,xhi)
            plt.ylim(ylo,yhi)
            
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
        width = 0.35 + 0.15

        Nc = y.shape[0]

        #cmap = matplotlib.cm.spectral #2 - 2d most distinct palette
        cmap = matplotlib.cm.Accent  # 1 - this provides the most distinct palette (tested to Nc=11)
        cmap = matplotlib.cm.tab20  # python3 - most distinctive palette (tested to Nc=12)
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
        left,right = plt.xlim(ind[0]-width,ind[-1]+width)
        #print('mpl_interface.stackedBarChart','left',left,'right',right)                  
        plt.xticks(ind, xlabels)
        loc,labs = plt.xticks()
        #print('mpl_interface.stackedBarChart','loc',loc,'labs',labs)
        if norm : plt.yticks(numpy.arange(0,f,0.10))
        P = [a[0] for a in p]
        plt.legend( P, ylabels,loc='best',ncol=3, borderaxespad=0., borderpad=.2, handletextpad=0.2, columnspacing=0.4)
        Title = title
        if norm: Title += ' (Norm to unity)'
        plt.title(Title)
        plt.grid()
        if self.internal : plt.show()
        
        return Title
    def pie(self,x,labels,title=None,addValues=False,startangle=0.):
        '''
        plot pie chart
        with title positioned to avoid wedge labels
        return title so it can be used to generate filename for output

        if addValues is True, then write the value of x in the appropriate wedge

        autopct usage cribbed from 
        https://stackoverflow.com/questions/6170246/how-do-i-use-matplotlib-autopct
        '''

        if addValues:
            plt.pie(x,labels=labels,labeldistance=1.3,startangle=startangle,autopct=lambda p : f'{p:.1f}%\n({(p/100)*sum(x):.0f})',pctdistance=1.1)
        else:
            plt.pie(x,labels=labels,labeldistance=1.05,startangle=startangle)
        if title is not None : plt.title( title, y=1.05, loc='left', bbox={'pad':3, 'facecolor':'none'} )
        if self.internal : plt.show()
        return title
    def plot(self,X,Names,binwidth,byMonth=True,Title=None,debug=-1):
        '''
        make plots of the frequency of Names given abscissa values X in bins of width = binwidth, if byMonth = False. If byMonth = True, then bins are month long

        returns the object to plot

        first determine abscissa binning
        then create histograms for each unique entry in Names
        then enable readable legend that doesn't obscure points
        then set title and plot (or return info for plotting)
        '''

        tfmt = '%Y%m%d'
        tfmt2= '%Y%m%d%H%M%S'
        x1,x2 = min(X),max(X)
        if byMonth:
            y1,m1 = x1.year,x1.month
            y2,m2 = x2.year,x2.month
            bins = []
            for year in range(y1,y2+1):
                firstm, lastm = 1,12
                if year==y1 : firstm = m1
                if year==y2 : lastm = m2
                for month in range(firstm,lastm+1):
                    d = datetime.datetime.strptime('{:04}{:02}{:02}'.format(year,month,1),tfmt)
                    bins.append( d )
            lastday = calendar.monthrange(y2,m2)[1]
            d = datetime.datetime.strptime('{:04}{:02}{:02}{:02}{:02}{:02}'.format(y2,m2,lastday,23,59,59),tfmt2)
            bins.append(d)
            bins = numpy.array(bins)
        else:
            bins = numpy.arange(x1,x2+binwidth,binwidth)
        if debug > 0 : print('mpl_interface.plot byMonth',byMonth,'bins',bins)

        ymi,yma = -1.,0.
        for name in set(Names):
            x = []
            for u,v in zip(X,Names):
                if v==name : x.append( u )
            hist,edges = numpy.histogram(x,bins=bins)
            yma = max(yma,max(hist))
            e = []
            for a,b in zip(edges[:-1],edges[1:]):
                e.append(a + (b-a)/2.)

            plt.plot(e,hist,'o-',label=name)

        ## adjust ordinate limits to show zeros and to allow room for legend
        ## set # of columns for legend and size of text in legend
        ## create title 
        ymi = -abs(yma)/50.
        yma = 1.2*yma
        plt.ylim( (ymi, yma) )

        ncol = 1
        ncol = len(set(Names))//6+1
        fontsize = 'small'
        if len(set(Names))>12 : fontsize = 'x-small'
        plt.legend(loc='best',ncol=ncol,fontsize=fontsize)

        title = ' '.join(set(Names))
        if Title is not None : title = Title
        plt.title(title)
        plt.grid()
        if self.internal : plt.show()
        print('mpl_interface.plot title',title)
        return title
if __name__ == '__main__' :
    internal = True
    mpli = mpl_interface(internal=internal)

    testTimeHisto = True
    if testTimeHisto :
        t1 = datetime.datetime.strptime('20170201','%Y%m%d')
        t2 = datetime.datetime.strptime('20220325','%Y%m%d')
        dt = int((t2-t1).total_seconds())
        print('dt',dt,'seconds')
        issues = ['pigs','cats','flowers','dogs','gnus','kids','birds','foxes','armadillos','great white whales','porcupines','wolverines','penguins','chipmunks','arrogant humans']
        weights= [10,      20,     30,      1,     3,      4,     7,     2,         18,         9,                    22,        41,          77,        25,        104]
        ISSUES = []
        for i,w in zip(issues,weights):
            ISSUES.extend( [i for x in range(w)] )

        T,Y = [],[]
        N = 1000
        for i in range(N):
            idt = random.randint(0,dt)
            T.append(t1+datetime.timedelta(seconds=idt))
            Y.append(random.choice(ISSUES))


        binwidth = 365./12. * 3. # average days/month x 3 months
        binwidth = datetime.timedelta(days=binwidth)

        mpli.plot(T,Y,binwidth,byMonth=True,Title = 'every month')
        mpli.plot(T,Y,binwidth,byMonth=False, Title = 'in 3 month chunks')
        sys.exit('done')
        
        

    testPie = False
    if testPie :
        # https://stackoverflow.com/questions/25921503/generate-alphanumeric-random-numbers-in-numpy
        A,Z = numpy.array(["a","z"]).view("int32")
        LEN = 4
        for N in [10, 25, 35, 45, 55, 101]:

            k = [random.randint(1,30) for x in range(N)]
            l = numpy.random.randint(low=A,high=Z,size=N*LEN,dtype="int32").view(f"U{LEN}") # [str(x) for x in k]
            x,labels = k,l
            title = str(N) + 'wedges. this is the title. it is a very long title. \nand it cannot be used on this experiment because it extends too far'
            addValues = N<=25
            TT = mpli.pie(x,labels,title=title,addValues=addValues)
    
    testHisto = False
    if testHisto :
        Y = numpy.random.exponential(4.3,100)
        xlo,xhi = 0.,round(max(Y),False) # round up?
        xlo,xhi = xlo-0.5,xhi+1.5
        dx = 1.0
        nbin = int((xhi-xlo)/dx)
        for ulog in ['liny','logy']:
            mpli.histo(Y,xlo,xhi,nbin=nbin,title=str(nbin)+' bins',grid=True,logy=ulog)
            mpli.histo(Y,xlo,xhi,nbin=25,title='25 bins',grid=True,logy=ulog)
            for dx in [1.0]:
                mpli.histo(Y,xlo,xhi,dx=dx,title='bin size is '+str(dx),grid=False,logy=ulog)
        sys.exit('done with testHisto')

    testPlot2d = False
    if testPlot2d :
        ### square 2d plot
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
        Z = numpy.reshape(numpy.array(z),(nr,nc))
        xlabels = ['this is a '+q for q in  ['cow','horse','goat','pig','cat','dog','rat','awk']]
        ylabels = xlabels[:nr+1]
        xlabels = xlabels[:nc+1]
        mpli.plot2d(x,y,Z,xlabels=xlabels,ylabels=ylabels,title='Down at the farm')

        ### non-square
        nr = 3
        nc = 5
        x = numpy.arange(nc+1)
        y = numpy.arange(nr+1)
        z = []
        for ir in range(nr):
            for ic in range(nc):
                z.append( float(ir)*10 + float(ic) ) #numpy.random.random()*100. )
        Z = numpy.reshape(numpy.array(z), (nr, nc) )
        xlabels = ['cat','pig','dog','cow','fly','ant'][:nc]
        ylabels = ['various types of potted plants','pan-fried','soap dish','plate of shrimp, or just plate','bucket of slop'][:nr]
        mpli.plot2d(x,y,Z,xlabels=xlabels,ylabels=ylabels,title='just try this')
        sys.exit('end testPlot2d')

    testStackedBar = False
    ntest = -1
    if testStackedBar :
        ntest = 2
        for itest in range(ntest):
            ylabels = ['pony','chicken','dog','duck','goose','penguin','hippo','cat','turkey','kangaroo','wolverine','stegasaurus']
            N = len(ylabels)
            ylabels = ['this is a '+q for q in ylabels]
            x = [10., 20., 30., 40., 50.]
            if itest>0: x.extend( [60., 70., 80.] )
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
        sys.exit('end testStackedBar')


    listParts = False
    if listParts:
        fn = 'DATA/comp-users-forum_2021-01/107'
        if len(sys.argv)>1 : fn = sys.argv[1]
        mpli.listParts(fn)
        sys.exit('extractMsg listParts ' + fn)

