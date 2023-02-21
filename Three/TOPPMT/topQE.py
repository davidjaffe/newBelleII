#!/usr/bin/env python
'''


plot results of linear fits to relative QE vs accumulated charge from 1420_Inami_TOPPMT_20230219.pdf
20230221
'''
import numpy

import os

import sys
import math
import matplotlib.pyplot as plt
import numpy
from scipy.optimize import curve_fit

class topQE():
    def __init__(self):


        ### calibration of free ruler
        ### relative QE(%) = y-axis
        ### 100 = 0 pixels, 80 = 446 pixels
        ### Accumulated charge (mC/cm^2) = x-axis
        ### 0. = 0 pixels, 80 mC/cm2 = 604 pixels
        ### Ambient temp was 20C, then 40C, then back to 20C
        self.dataPx = {'20Ca': [ (0,0), ( 46, 18), ( 83, 36),( 127, 59), ( 212, 104)],
                       '40C' : [ (242, 204), ( 267, 246), ( 295, 275), (319, 304), (347, 331), (376, 354), (398, 377), (426, 370), (434, 410) ],
                       '20Cb': [ (469, 374), (498, 364), (516,372), (550,383), (551,402), (583,406), (623,408), (659, 421) ] }

        ### assume uncertainty in QE is same for all points
        ### measure length of error bars for one point
        self.uncQE = 0.5*(33.-8.)*(100.-80.)/(446.-0.)

        self.colors = {'20Ca': 'blue', '40C' :'black', '20Cb' : 'red'}
        
        ### transform to relative QE vs accumulated charge
        self.data = {}
        for temp in self.dataPx:
            self.data[temp] = []
            pairs = self.dataPx[temp]
            for pair in pairs:
                x,y = pair
                X = (x - 0.)*(80.-0.)/(604.-0.)
                Y = 100. - (y)*(100. - 80.)/(446. - 0.)
                #print(temp,'x,y',x,y,'X,Y',X,Y)
                self.data[temp].append( (X,Y) )

        return

    def toNPA(self,a):
        return numpy.array(a)
    def linear(self, x, m, b):
        return m*x + b
    def getData(self,temp='20Ca'):
        '''
        return numpy arrays X,Y,dY of data for given temperature temp
        '''
        X,Y,dY = [],[],[]

        pairs = self.data[temp]
        for pair in pairs:
            x,y = pair
            X.append( x )
            Y.append( y )
            dY.append( self.uncQE )
        X,Y,dY = self.toNPA(X), self.toNPA(Y), self.toNPA(dY)
        return X,Y,dY
    def main(self):


        
        for temp in self.data:
            X,Y,dY = self.getData(temp)
            param, cov = curve_fit(self.linear, X,Y,sigma=dY)
            #print('topQE.main',temp,'results of linear fit, param',param,'cov',cov)
            m,b = param
            dm,db = math.sqrt(cov[0,0]),math.sqrt(cov[1,1])
            text = ' QE = {:.2f}({:.2f})*Q + {:.1f}({:.1f})'.format(m,dm,b,db)
            y0,y1 = m*X[0]+b,m*X[-1]+b
            plt.plot( (X[0],X[-1]), (y0,y1), linestyle='dashed',color='green')
            plt.errorbar(X,Y,fmt='o',yerr=dY,color = self.colors[temp],label=temp+text)

            plt.fill_between( (X[0],X[-1]), 80., 100,  color=self.colors[temp],alpha=0.2)
                             

        plt.title('JT0901')
        plt.legend(loc='best')
        plt.grid()
        plt.xlabel('Accumulated output charge (Q) [mC/cm^2]')
        plt.ylabel('Relative QE [%]')
        plt.show()
        sys.exit('--------------> All done')

        ## do linear fit to the first 3 points
        param, cov = curve_fit(self.linear, x[:3], LY[:3], sigma=dLY[:3])
        print('topQE.main results of linear fit, param',param,'cov',cov)

        ## generate a family of fit parameters consistent with
        ## the fit results
        size = 500
        p = numpy.random.multivariate_normal(param,cov,size=size)

            
        
        X = numpy.linspace(min(x)/10.,max(x),1000)
        m, b = self.lfit['slope'][0],self.lfit['intercept'][0]
        Y = m*X+b

        for xma,rng in zip([101.,10.1],['Xfull','Xpartial']):
            for yscale in ['linear','log']:
                yw = 'Y'+yscale
                for xscale in ['linear','log']:
                    words = rng+yw+'X'+xscale 

                    ### plot data
                    plt.errorbar(x,LY,fmt='o',yerr=dLY,color='black',label='LBL')

                    ### plot BNL data
                    plt.errorbar(BNLx,BNLLY,fmt='o',yerr=dBNLLY,color='blue',label='BNL')

                    ### draw family of fit results as grey band
                    for pair in p:
                        m,b = pair
                        YY = m*X+b
                        plt.plot(X,YY,color='grey',linestyle='solid',alpha=0.1)
                    ### main fit result
                    plt.plot(X,Y,'r-')

                    plt.title('absolute LY arXiv:2006.00173 table 1')
                    plt.grid()
                    plt.legend(loc='best')
                    
                    plt.xlabel('% Concentration')
                    plt.ylabel('Light yield (ph/MeV/% conc)')
                    plt.xscale(xscale)
                    plt.yscale(yscale)
                    if xscale=='linear': plt.xlim(-1.,xma)
                    if yscale=='linear' and xma<100. : plt.ylim(0.,2000.) 
                    png = 'LINEARLY_FIGURES/topQE_arXiv2006.00173_'+words+'.png'
                    plt.savefig(png)
                    print('topQE.main Wrote',png)
                    plt.show()

        
        return
if __name__ == '__main__' :
    P = topQE()
    P.main()
    
