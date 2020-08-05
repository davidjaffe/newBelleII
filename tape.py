#!/usr/bin/env python
'''
compare bnl tape usage and integrated luminosity 
20200804
'''
import sys
import math
import csv
import numpy
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime


class tape():
    def __init__(self):

        self.figDir = ''
        self.drawToFile = False
        return
    def main(self):
        Ldate,Llum = [],[]
        with open('/Users/djaffe/Desktop/IntLum.csv','rb') as lumfile:
            lumreader = csv.reader(lumfile)
            for row in lumreader:
                #print ', '.join(row)    
                a,b = row
                #print a,b
                if a.lower()!='date':
                    Ldate.append(datetime.datetime.strptime(a,'%m/%d/%Y'))
                    Llum.append(float(b))
        Tdate,TB = [],[]
        with open('/Users/djaffe/Desktop/TapeUsage.csv','rb') as tapefile:
            tapereader = csv.reader(tapefile)
            for row in tapereader:
                #print ', '.join(row)
                a,b = row
                #print a,b
                if a!='Date':
                    Tdate.append(datetime.datetime.strptime(a,'%m/%d/%Y'))
                    TB.append(float(b))

        maxTB = max(TB)
        maxIL = max(Llum)
        rat = maxTB/maxIL
        print 'tape.main total TB',maxTB,'total int.lum 1/fb',maxIL,'TB/invfb',rat
        datemin = min(min(Ldate),min(Tdate))
        datemax = max(max(Ldate),max(Tdate))
        singles = False
        if singles:
            self.drawIt(Ldate,Llum,'date','int.lum.1/fb','belle ii lum',mark='o',xlims=[datemin,datemax])
            self.drawIt(Tdate,TB,'date','Tape (TB)','BNL tape usage',mark='+',xlims=[datemin,datemax])

        self.drawBoth(Ldate,Llum,Tdate,TB,datemin,datemax)
        return
    def drawBoth(self,xL,yL,xT,yT,datemin,datemax):
        title = 'IntLum and BNL tape usage'
        #plt.clf()
        fig, (axL,axT) = plt.subplots(2,1)
        #plt.grid()
        fig.suptitle(title)

        
        X = numpy.array(xL)
        Y = numpy.array(yL)
        axL.scatter(X,Y,color='b',marker='o',label='lum 1/fb')
        axL.set_ylabel('lum 1/fb')
        X = numpy.array(xT)
        Y = max(yL)/max(yT)*numpy.array(yT)
        axL.scatter(X,Y,color='r',marker='+',label='scaled tape volume')
        axL.legend(loc='upper left')
        X,Y = numpy.array(xT),numpy.array(yT)
        axT.scatter(X,Y,color='r',marker='o')
        axT.set_ylabel('tape TB')
        axL.set_xlim([datemin,datemax])
        axT.set_xlim([datemin,datemax])
        axL.grid()
        axT.grid()
        axT.xaxis.set_major_formatter(mdates.DateFormatter('%m-%y'))
        axL.xaxis.set_major_formatter(mdates.DateFormatter('%m-%y'))

        #plt.xlabel('Date')

        #plt.show()
        pdf = self.figDir + title.replace(' ','_') + '.pdf'
        plt.savefig(pdf)
        print 'tape.main wrote',pdf 
        return
        
    def drawIt(self,x,y,xtitle,ytitle,title,ylog=False,xlims=None,ylims=None,mark='o-',label=''):
        '''
        draw graph defined by x,y

        '''
        plt.clf()
        plt.grid()
        plt.title(title)

        X = numpy.array(x)
        Y = numpy.array(y)
        plt.plot(X,Y,mark,label=label)
        plt.xlabel(xtitle)
        plt.ylabel(ytitle)
        if ylog : plt.yscale('log')
        if xlims is not None: plt.xlim(xlims)
        if ylims is not None: plt.ylim(ylims)

        plt.legend(loc='best')

        if self.drawToFile:
            fn = self.titleAsFilename(title)
            figpdf = 'FIG_'+fn + '.pdf'
            figpdf = self.figDir + figpdf
            plt.savefig(figpdf)
            print 'combiner.drawIt wrote',figpdf
        else:
            plt.show()
        return    
    def drawMany(self,x,y,xtitle,ytitle,title,ylog=False,xlims=None,ylims=None,loc='best'):
        '''
        draw many graphs with same abscissa and different ordinate values on same plot defined by x,y
        y = dict
        ytitle = keys of dict

        '''
        fig,ax = plt.subplots()
        plt.grid()
        plt.title(title)
        major = 1.
        if xlims is not None:
            if xlims[1]-xlims[0]<=2: major = (xlims[1]-xlims[0])/10
        ax.xaxis.set_major_locator(MultipleLocator(major))
        minor = major/5.
        ax.xaxis.set_minor_locator(MultipleLocator(minor))
        if self.debug>1: print 'combiner.drawMany major,minor',major,minor,'xlims',xlims


        ls = ['-','--','-.',':','-','--',':']
        ls.extend(ls[::-1])
        c  = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        c.extend(c)
        
        X = numpy.array(x)
        for i,key in enumerate(ytitle):
            Y = numpy.array(y[key])
            ax.plot(X,Y,linestyle=ls[i],color=c[i],label=key)

        plt.xlabel(xtitle)
#        plt.ylabel(ytitle)
        if ylog : ax.yscale('log')
        if xlims is not None: plt.xlim(xlims)
        if ylims is not None: plt.ylim(ylims)

            
        ax.legend(loc=loc)
        if self.drawToFile : 
            fn = self.titleAsFilename(title)
            figpdf = 'FIG_'+fn + '.pdf'
            figpdf = self.figDir + figpdf
            plt.savefig(figpdf)
            print 'combiner.drawMany wrote',figpdf
        else:
            plt.show()
        return            
if __name__ == '__main__':
    t = tape()
    t.main()
