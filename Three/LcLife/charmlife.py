#!/usr/bin/env python
'''
lifetime of lambda c from cascade c

20220222
'''
import sys,os
import matplotlib.pyplot as plt
import numpy
import math


class charmlife():
    def __init__(self):
        # lifetimes in fs
        self.charm = [r'$D^+$',r'$D^0$', r'$\Lambda_c^+$', r'$\Omega_c$']
        # PDG2020+2021 update
        self.life  = [ 1040., 410.1, 202.4, 268.]
        self.dlife = [    7.,   1.5,   3.1,  26.]
        # previous Omega c lifetime measurements
        # uncertainties are symmetrized by taking average of up,down unc and summing stat+syst in quadrature
        self.omegacExpt = ['FOCUS', 'WA89', 'E687']
        self.omegacLife = [     72.,    55.,     86.]
        self.omegacDLife= [math.sqrt(11.*11.+11.*11.),
                          math.sqrt(12.*12.+20.5*20.5),
                          math.sqrt(23.5*23.5+28.*28)]
            # D+,D0 PRL 127, 211801 (2021).
            # Jake's PRL draft v3-4
            # Nisar's prez to Charm WG 20220427 BLINDED
        self.B2name  = ['Belle II\n'+x for x in ['published','published','prelim','blinded']]
        
        self.B2life  = [1030.4, 410.5, 203.20, 299.6]
        self.B2dlife = [math.sqrt(4.7*4.7+3.1*3.1),math.sqrt(1.1*1.1+0.8*0.8), math.sqrt(0.89*0.89+0.77*0.77),math.sqrt(50.6*50.6+13*13)]
        print('charmlife.__init__ Completed')
            
        return
    def main(self):
        x0 = 0.
        x,dx,xstep = x0,1.,8.
        Gname,X,Y,dY = [],[],[],[]
        Title = []
        
        
        print('\nPDG2020 + 2021 update')
        for i,tau in enumerate(self.life):
            name = self.charm[i]
            dtau = self.dlife[i]
            print('{} {:.1f}({:.1f}) fs'.format(name,tau,dtau))
            X.append(x)
            x += xstep
            Y.append(tau)
            dY.append(dtau)
            Title.append(name)
            Gname.append('PDG')
            
        print('\nOmega_c lifetimes')
        x -= dx + xstep
        for i,tau in enumerate(self.omegacLife):
            name = self.omegacExpt[i]
            dtau = self.omegacDLife[i]
            print('{} {:.1f}({:.1f}) fs'.format(name,tau,dtau))
            X.append(x)
            x -= dx
            Y.append(tau)
            dY.append(dtau)
            Gname.append(name)
            
        print('\nBelle II')
        x = x0 + dx
        for i,tau in enumerate(self.B2life):
            name = self.charm[i]
            dtau = self.B2dlife[i]
            print('{} {:.1f}({:.1f}) fs'.format(name,tau,dtau))
            X.append(x)
            x += xstep
            Y.append(tau)
            dY.append(dtau)
            Gname.append(self.B2name[i])


        NY = 4
        if NY==2: 
            fig, ax = plt.subplots(2,NY)#1,4)
        else:
            fig, ax = plt.subplots(1,4)

        TIGHT = False
        if not TIGHT: 
            fig.subplots_adjust(wspace=.5)

        if NY==2:
            A = [ax[0,0],ax[1,0],ax[0,1],ax[1,1]]
        else:
            A = ax


        yrange = [ [1000.,1060.],  [405.,415.] , [190.,215.], [0.,450.] ]
        Used = []

        for J,a in enumerate(A):
            r = yrange[J]
            title = Title[J]
            
            U,V,dV,Name = [],[],[],[]
            for i,name in enumerate(Gname):
                x,y,dy = X[i],Y[i],dY[i]
                if r[0]<=y<=r[1] and y not in Used:
                    Used.append(y)
                    U.append(x)
                    V.append(y)
                    dV.append(dy)
                    Name.append(name)
            print('r',r,'len(U)',len(U),'U',U,'V',V,Name)
            
            a.errorbar(U,V,yerr=dV,label=Name,linestyle='none',marker='o')
            A[0].set_ylabel('Lifetime (fs)',fontsize=15)
            
            for i,name in enumerate(Name):
                if NY==2:  # labels beside points
                    xbit,ybit= 0.1,0.
                    va = 'center'
                    ha = 'center'
                else: # labels above points
                    xbit,ybit=0.,1.15*dV[i]
                    va = 'bottom'
                    ha = 'center'
                x,y = U[i]+xbit,V[i]+ybit
                a.text(x,y,name,rotation=90,verticalalignment=va,horizontalalignment=ha,fontsize=12)
                #print('x,y,name',x,y,name)

            a.set_title(title,fontsize=15)
            a.tick_params(axis='x',which='both', bottom=False,top=False,labelbottom=False)          # changes apply to the x-axis, both major and minor ticks are affected,  ticks along the bottom edge are off,  ticks along the top edge are off
            

        hx = dx/2.
        A[0].set_xlim((x0-hx,x0+1.5*dx))
        A[0].set_ylim(yrange[0])


        A[1].set_xlim((x0+xstep-hx,x0+xstep+1.5*dx))
        A[1].set_ylim(yrange[1])

        A[2].set_xlim((x0+2*xstep-hx,x0+2*xstep+1.5*dx))
        A[2].set_ylim(yrange[2])

        A[3].set_xlim((x0+3*xstep-4*dx,x0+3*xstep+2*dx))
        A[3].set_ylim(yrange[3])

        if TIGHT: plt.tight_layout()
        pdf = 'charmlife.pdf'
        plt.savefig(pdf)
            
        plt.show()
                    
        
        return
    
if __name__ == '__main__' :
    L = charmlife()
    L.main()

