#!/usr/bin/env python
'''
luminosity plotting, etc. 
20191220
'''
import math
import sys,os
#import random

import datetime
import numpy
import copy

import re

import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,  AutoMinorLocator)


class lumi():
    def __init__(self):

        self.debug = 1

        self.drawToFile = True

        self.barn = 1.e-24 # cm2
        self.fb = 1.e-15*self.barn # b2parser = b2parser.b2parser()

        self.year = 365.*24.*60.*60.
        self.figDir = 'FIGURES/'
        
        return
    def drawMany(self,x,y,xtitle,ytitle,title,ylog=False,xlims=None,ylims=None,loc='best',legendTitle='',ylabel=''):
        '''
        draw many graphs with same abscissa and different ordinate values on same plot defined by x,y
        y = dict
        ytitle = keys of dict

        '''
        fig,ax = plt.subplots()
        plt.rcParams.update({'font.size': 12, 'font.weight':'normal'})
        plt.rcParams["legend.labelspacing"] = 0.5/5
        plt.grid()
        plt.title(title)
        if 1:
            major = 1.
            if xlims is not None:
                if xlims[1]-xlims[0]<2: major = (xlims[1]-xlims[0])/10
            ax.xaxis.set_major_locator(MultipleLocator(major))
            minor = major/5.
            ax.xaxis.set_minor_locator(MultipleLocator(minor))
            print 'combiner.drawMany major,minor',major,minor,'xlims',xlims
            major = 250.
            minor = 100
            ax.yaxis.set_major_locator(MultipleLocator(major))
            ax.yaxis.set_minor_locator(MultipleLocator(minor))


        ls = ['-','--','-.',':','-','--']
        ls.extend(ls)
        c  = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        c.extend(c)
        
        X = numpy.array(x)
        for i,key in enumerate(ytitle):
            Y = numpy.array(y[key])
            ax.plot(X,Y,linestyle=ls[i],color=c[i],label=key)

        plt.xlabel(xtitle)
        plt.ylabel(ylabel)
#        if ylog : ax.yscale('log')
        if xlims is not None: plt.xlim(xlims)
        if ylims is not None: plt.ylim(ylims)

        ax.legend(loc=loc,title=legendTitle)
        if self.drawToFile : 
            fn = self.titleAsFilename(title)
            figpdf = 'FIG_'+fn + '.pdf'
            figpdf = self.figDir + figpdf
            plt.savefig(figpdf)
            print 'combiner.drawMany wrote',figpdf
        else:
            plt.show()
        return                
    def titleAsFilename(self,title):
        '''
        return ascii suitable for use as a filename
        list of characters to be replaced is taken from https://stackoverflow.com/questions/4814040/allowed-characters-in-filename
        '''
        r = {'_': [' ', ',',  '\\', '/', ':', '"', '<', '>', '|'], 'x': ['*']}
        filename = title
        filename = ' '.join(filename.split()) # substitutes single whitespace for multiple whitespace
        for new in r:
            for old in r[new]:
                if old in filename : filename = filename.replace(old,new)
        return filename
    def drawIt(self,x,y,xtitle,ytitle,title,figDir=None,ylog=False,xlims=None,ylims=None,linfit=False):
        '''
        draw graph defined by x,y

        '''
        debug = False
        if debug: print 'climate.drawIt len(x),len(y)',len(x),len(y),xtitle,ytitle,title,'xlimits',xlims,'ylimits',ylims
        if debug: print 'climate.drawIt x',x,'\ny',y
        plt.clf()
        plt.grid()
        plt.title(title)
        figpdf = 'FIG_'+title.replace(' ','_') + '.pdf'
        if debug: print 'climate.drawIt figpdf',figpdf

        X = numpy.array(x)
        Y = numpy.array(y)
        if debug: print 'climate.drawit X',X,'\nY',Y

        plt.plot(X,Y,'o-')

        plt.xlabel(xtitle)
        plt.ylabel(ytitle)
        if ylog : plt.yscale('log')
        if debug: print 'climate.drawit ylog',ylog
        if xlims is not None : plt.xlim(xlims)
        if ylims is not None : plt.ylim(ylims)

            

        if debug: print 'climate.drawit figDir',figDir
        
        if figDir is not None:
            figpdf = figDir + figpdf
            plt.savefig(figpdf)
            print 'climate.drawIt wrote',figpdf
        else:
            if debug: print 'climate.drawit show',title
            plt.show()
        return
    def main(self):
        '''
        plot integrated luminosity v months for given instantaneous lumi
        '''
        months = numpy.array( range(0,25) )
        instlum = numpy.array( [1.e34, 1.5e34, 2.0e34, 3.0e34, 4.0e34, 6.0e34, 8.0e34, 10.e34, 15.e34] )
        unit = 1.e34

        intL = {}
        skey = []
        for L in instlum:
            u = str(L/unit)# + 'e34/cm2/s'
            intL[u] = L * self.fb *self.year * months / 12.
            skey.append(u)
        self.drawMany(months,intL,'months',skey,'Integrated lum vs months',ylims=[0.,2501.],legendTitle='Instantaneous Lum.\n(1e34/cm2/s)',ylabel='Integrated luminosity(1/fb)')
        return

if __name__ == '__main__' :

    lu = lumi()
    lu.main()
    
