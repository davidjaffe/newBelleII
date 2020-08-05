#!/usr/bin/env python
'''
climate and airfare related calculations
201909xx
'''
import math
import sys,os
#import random

import datetime
import numpy
import copy

import re
import glob # used in __init__

from lxml.html import parse  # used by readB2GM

import matplotlib.pyplot as plt

import b2parser

class climate():
    def __init__(self):

        self.debug = 1

        self.b2parser = b2parser.b2parser()

        self.GADfile = 'CDATA/GlobalAirportDatabase/GlobalAirportDatabase.txt'
        self.Airfarefile = 'CDATA/Airfares_CityPairs_20190929.csv'
        self.CO2file = 'CDATA/CO2_between_airports_20191013.csv'
        self.figdir = 'FIGURES/'

        self.B2MembersFile = 'CDATA/BelleII_members_20200209.csv' ###'CDATA/BelleII_members_20190929.csv'
        self.B2InstitutionsFile = 'CDATA/BelleII_institutions_20190929.csv'
        self.B2InstitutionsFile = 'CDATA/BelleII_institutions_20200209.csv' ###'CDATA/BelleII_institutions_20190929.csv'

        
        # define input files with B2GM data. require them to be .htm or .html files
        files = glob.glob("CDATA/*B2GM*")
        files.sort()
        self.B2GMfiles = []
        for f in files:
            if '.htm' in f: self.B2GMfiles.append(f)
        print 'climate.__init__ will process the following B2GM attendance files '
        for a in self.B2GMfiles: print a
        print '\n'
            

        self.Legs = {}
        self.Legs[1] = ['nonstop','non-stop','non stop']
        self.Legs[2] = ['onestop','one-stop','one stop']
        self.Legs[3] = ['2 stops','two stop','two-stop','two-stops','two stops']

        self.earthRadius = 6371. # km according to duck-duck-go
        self.earthToMoon = float(385000.6) # time-average earth-moon distance according to https://en.wikipedia.org/wiki/Lunar_distance_(astronomy)
        
        self.originalTeamList = ['Arizona Diamondbacks',
                          'Atlanta Braves',
                          'Baltimore Orioles',
                          'Boston Red Sox',
                          'Chicago Cubs',
                          'Chicago White Sox',
                          'Cincinnati Reds',
                          'Cleveland Indians',
                          'Colorado Rockies',
                          'Detroit Tigers',
                          'Miami Marlins',
                          'Houston Astros',
                          'Kansas City Royals',
                          'Los Angeles Angels of Anaheim',
                          'Los Angeles Dodgers',
                          'Milwaukee Brewers',
                          'Minnesota Twins',
                          'New York Mets',
                          'New York Yankees',
                          'Oakland Athletics',
                          'Philadelphia Phillies',
                          'Pittsburgh Pirates',
                          'St. Louis Cardinals',
                          'San Diego Padres',
                          'San Francisco Giants',
                          'Seattle Mariners',
                          'Tampa Bay Rays',
                          'Texas Rangers',
                          'Toronto Blue Jays',
                          'Washington Nationals']
        # team names altered to serve as keys and team airport city
        self.teams = {'Arizona_Diamondbacks':'Phoenix',
                          'Atlanta_Braves':'Atlanta',
                          'Baltimore_Orioles':'Baltimore',
                          'Boston_Red_Sox':'Boston',
                          'Chicago_Cubs':'Chicago',
                          'Chicago_White_Sox':'Chicago',
                          'Cincinnati_Reds':'Cincinnati',
                          'Cleveland_Indians':'Cleveland',
                          'Colorado_Rockies':'Denver',
                          'Detroit_Tigers':'Detroit',
                          'Miami_Marlins':'Miami',
                          'Houston_Astros':'Houston',
                          'Kansas_City_Royals':'Kansas City',
                          'Los_Angeles_Angels_of_Anaheim':'SANTA ANA',
                          'Los_Angeles_Dodgers':'Los Angeles',
                          'Milwaukee_Brewers':'Milwaukee',
                          'Minnesota_Twins':'Minneapolis',
                          'New_York_Mets':'New York',
                          'New_York_Yankees':'New York',
                          'Oakland_Athletics':'Oakland',
                          'Philadelphia_Phillies':'Philadelphia',
                          'Pittsburgh_Pirates':'PITTSBURGH (PENNSYLVA)',
                          'St._Louis_Cardinals':'St. Louis',
                          'San_Diego_Padres':'San Diego',
                          'San_Francisco_Giants':'San Francisco',
                          'Seattle_Mariners':'Seattle',
                          'Tampa_Bay_Rays':'Tampa',
                          'Texas_Rangers':'DALLAS-FORT WORTH',
                          'Toronto_Blue Jays':'Toronto',
                          'Washington_Nationals':'Washington'}
        
        # sort keys that are team names to be alphabetical
        self.teamList = self.teams.keys()
        self.teamList.sort()

        self.position = None
        
        
        return
    def readGlobalAirportDatabase(self):
        '''
        gets latitude, longitude of cities with MLB teams
        Data retrieved 20190915 from partow.net/miscellaneous/airportdatabase/#Download
        Field	Name	Type
01	ICAO Code	String (3-4 chars, A - Z)
02	IATA Code	String (3 chars, A - Z)
03	Airport Name	String
04	City/Town	String
05	Country	String
06	Latitude Degrees	Integer [0,360]
07	Latitude Minutes	Integer [0,60]
08	Latitude Seconds	Integer [0,60]
09	Latitude Direction	Char (N or S)
10	Longitude Degrees	Integer [0,360]
11	Longitude Minutes	Integer [0,60]
12	Longitude Seconds	Integer [0,60]
13	Longitude Direction	Char (E or W)
14	Altitude	Integer [-99999,+99999]
(Altitude in meters from mean sea level)
15	Latitude Decimal Degrees	Floating point [-90,90]
16	Longitude Decimal Degrees	Floating point [-180,180]
'''
        f = open(self.GADfile,'r')
        self.position = {}
        for line in f:
            s = line[:-1].split(':') # remove \n
            if self.debug>2: print 'climate.readGAD s',s
            code,airport,city,country,latitude,longitude = s[1],s[2],s[3],s[4],float(s[14]),float(s[15])
            if s[1]!='N/A': # Two Washington airports have lat,long=0,0
                names = self.mlbTeam(city,country)
                if names is not None:
                    for team in names:
                        self.position[team] = (latitude,longitude)
        f.close()
        print 'readGlobalAirportDatabase Found',len(self.position),'mlb cities'
        return
    def getGAD(self,reportDup=False):
        '''
        return dict of Global Airport Data in form dict[XXX] where XXX is three letter code IATA of airport

        GAD validity checks:
        IATA code not N/A
        city not N/A
        IATA code matches last 3 letters in IACO code (Akron and Akure, Nigeria have same IATA code AKR)

        set reportDup = True to report duplicate IATA
        '''
        f = open(self.GADfile,'r')
        GAD = {}
        for line in f:
            s = line[:-1].split(':')
            IACO = s[0]
            IATA = s[1]
            city = s[2]
            if IATA!='N/A' and city!='N/A':

                if IATA in GAD:   # already in dict, is this the best match?
                    if IATA==IACO[1:]: # this is better match
                        GAD[IATA] = s
                    elif IATA==GAD[IATA][0][1:]: # already have best match
                        pass
                    else:
                        if reportDup: print 'climate.readGAD DUPLICATE IATA',IATA,'in line',line[:-1]
                        #sys.exit('climate.readGAD ERROR IATA '+IATA+' IACO '+IACO)
                else:
                    GAD[IATA] = s
        print 'climate.getGAD Processed',self.GADfile
        f.close()
        return GAD
    def findIATA(self,GAD,city,country=None,debug=0):
        '''
        given dict of Global Airport Data
        return IATA code corresponding to input city, country
        else return None
        '''
        icity = 3
        icountry = 4
        ucity = city.upper()
        ucountry = None
        if country is not None: ucountry = country.upper()
        for IATA in GAD:
            CITY,COUNTRY = GAD[IATA][icity],GAD[IATA][icountry]
            if ucountry is None: COUNTRY = None
            if debug>1: print 'climate.findIATA ucity',ucity,'ucountry',ucountry,'CITY',CITY,'COUNTRY',COUNTRY
            if CITY==ucity and COUNTRY==ucountry :
                if debug>0: print 'climate.findIATA ucity',ucity,'ucountry',ucountry,'matched to CITY',CITY,'COUNTRY',COUNTRY
                return IATA
        if debug>0: print 'climate.findIATA ucity',ucity,'ucountry',ucountry,' NO MATCH'
        return None
    def readAirFares(self,debug=0):
        '''
        Return dict[city1] = [fare,city1,city2] of airfares for city1,city2 pairs where city2==Tokyo 
        from airfare file
        column contents in airfare file are
        0 = city1
        1 = city2
        3 = alternate name for city1 (eg., Bombay for Mumbai)
        2 = fare in USD
        4 = comments (airline nonstop or onestop)
        '''
        f = open(self.Airfarefile,'r')
        print 'climate.readAirFares from',self.Airfarefile
        AirFares = {}
        for line in f:
            if 'Origin' not in line:
                s = line[:-1].split(',')
                s = re.split(",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", line[:-1])
                if debug>0:
                    print 'climate.readAirFares line[:-1]',line[:-1]
                    print 'climate.readAirFares s',s
                if s[0]!=' ':    # odd parsing of last entry requires a blank line(?)
                    city1 = s[0].strip()
                    city2 = s[1]
                    acity1= s[3]
                    fare  = float(s[2])
                    comments = s[4]
                    if city1 in AirFares:
                        print 'climate.readAirFares ERROR line',line[:-1]
                        sys.exit('climate.readAirFares ERROR Duplicate city1 '+city1)
                    else:
                        AirFares[city1] = [fare,city1,city2,acity1,comments]
        f.close()
        print 'climate.readAirFares',len(AirFares),'airfares processed from',self.Airfarefile
        if debug>0:
            print 'climate.readAirFares city/fare/city2/acity1/comments'
            for key in sorted(AirFares.keys()):
                fare,city1,city2,acity1,comments = AirFares[key]
                print '{0}/{1:.0f}/{2}/{3}/{4}'.format(city1,fare,city2,acity1,comments)
        return AirFares
                    
    def mlbTeam(self,city,country):
        '''
        return list of MLB team names if city,country combination is MLB city, otherwise None
        '''
        names = []
        if country=='USA' or country=='CANADA':
            for team in self.teams:
                if city.lower() == self.teams[team].lower():
                    if self.debug>1:
                        print 'climate.mlbTeam Match',city,country,'to',team,self.teams[team]
                    names.append(team)
        if len(names)>0: return names
        return None
    def getTeamPosition(self):
        '''
        assign longitude,latitude to each team
        '''
        self.readGlobalAirportDatabase()
        print '\nclimate.getTeamPosition: report latitude,longitude for airport near each team home'
        for team in self.teamList:
            if team in self.position:
                print team,self.position[team],
            else:
                print team,'**** NO POSITION *****'
        print '\n'
        return
    def getDistances(self):
        '''
        get distances between all pairs of teams
        return dict of distances of all pairs of teams
        '''
        pairDistance = {}
        n = 0
        if self.debug>1: print '\nDistance between all teams'
        
        for i1,team1 in enumerate(self.teamList):
            for team2 in self.teamList[i1+1:]:
                distance = self.haversine( self.position[team1],self.position[team2] )
                pairDistance[n] = [distance,team1,team2]
                if self.debug>1: print n,distance,team1,team2
                n += 1
        spD = sorted(pairDistance.items(), key=lambda x:x[1])
        print 'climate.getDistances Nearest',spD[0],'Farthest',spD[-1]
        return pairDistance
    def reDistribute(self):
        '''
        investigate schemes to redistribute teams to divisions
        '''
        pairDistance = self.getDistances() # pairDistance[n] = [distance,team1,team2]
        cities = ['Seattle','Miami','Chicago','Boston']
        anchors = []
        for city in cities:
            for team in self.teamList:
                if city in team:
                    anchors.append(team)
                    break
        print '\nclimate.reDistribute anchor teams',anchors
        for anchor in anchors:
            pD = {}
            for n in pairDistance:
                d,t1,t2 = pairDistance[n]
                if anchor==t1: pD[t2] = d
                if anchor==t2: pD[t1] = d
            spD = sorted(pD.items(), key=lambda x:x[1])
            print '\nclimate.reDistribute anchor',anchor,'\nteams',spD[:8]
        return
        
    def haversine(self,coord1, coord2):
        R = 6372800  # Earth radius in meters
        R = R/1000. # radius in km
        lat1, lon1 = coord1
        lat2, lon2 = coord2

        phi1, phi2 = math.radians(lat1), math.radians(lat2) 
        dphi       = math.radians(lat2 - lat1)
        dlambda    = math.radians(lon2 - lon1)

        a = math.sin(dphi/2)**2 + \
            math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2

        return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))
    def test(self):
        london_coord = 51.5073219,  -0.1276474
        cities = {
            'berlin': (52.5170365,  13.3888599),
            'vienna': (48.2083537,  16.3725042),
            'sydney': (-33.8548157, 151.2164539),
            'madrid': (40.4167047,  -3.7035825) 
            }

        for city, coord in cities.items():
            distance = self.haversine(london_coord, coord)
            print(city, distance)
        return
    def readB2I(self,debug=0):
        '''
        read Belle II institutions lists to get inst names, country, city
        return dict[short name] = [city,country,long name, short name]

        20200209 The .csv file produced by B2MMS places names in double quotes, so they get removed here 
        '''

        f = open(self.B2InstitutionsFile,'r')
        B2Inst = {}
        for line in f:
            if 'Postal' not in line: # avoids header
                s = line[:-1].split(',')
                sname = s[0].replace('"','')
                lname = s[1].replace('"','')
                country = s[4].replace('"','')
                city = s[5].replace('"','')
                B2Inst[sname] = [city,country,lname,sname]
                if debug>1: print 'climate.readB2I sname',sname,'B2Inst[sname]',B2Inst[sname]
        f.close()
        print 'climate.readB2I Processed',len(B2Inst),'institutions in',self.B2InstitutionsFile
        if debug>0 :  print 'climate.readB2I B2Inst.keys', '%s' % ', '.join(map(str, sorted(B2Inst.keys())))
        return B2Inst
    def readB2M(self):
        '''
        read Belle II members to get Belle II ID, name and institution name
        return dicts
        B2Members[B2id] =[firstname,middlename,lastname,lastnameprefix,inst]
        B2MemberEmail[B2id] = email
        20200209 The .csv file produced by B2MMS places names in double quotes, so they get removed here
        '''
        debug = 0
        f = open(self.B2MembersFile,'r')
        B2Members = {}
        B2MemberEmail = {}
        qqq = '"""' # 3 double quote surrounds short name of institution
        for line in f:
            if 'B2id' not in line: # avoids header
                s = line[:-1].split(',')
                for i,x in enumerate(s):
                    y = x.replace('"','')
                    if y=='-': y = ''
                    s[i] = y
                B2id = s[0]
                firstn = s[1]
                lastn  = s[2]
                middlen= s[3]
                lastnpre=s[4]
                email  = s[5]
                sname  = s[11].replace('"','') # institution short name (this does not always work because some fields have ',' in them)
                j1 = line.find(qqq)
                j2 = j1+1 + line[j1+1:].find(qqq)
                sname = line[j1+len(qqq):j2]
                B2Members[B2id] = [firstn,middlen,lastn,lastnpre,sname]
                B2MemberEmail[B2id] = email
                if debug>0: print 'climate.ReadB2M B2id',B2id,'B2Members[B2id]',B2Members[B2id],'B2MemberEmail',B2MemberEmail
        f.close()
        print 'climate.ReadB2M Processed',len(B2Members),'members in',self.B2MembersFile
        return B2Members, B2MemberEmail
    def readB2GM(self,B2GMfile):
        '''
        return list of [name1,name2,institution] of B2GM participants taken from various files. Institution may be missing from some files.

        for Oct 2019 B2GM: 
             return list of name1,name2 of cut/paste of B2GM participants 
             https://indico.belle2.org/event/971/registrations/participants, as of 20190929
        for June 2019 B2GM and earlier AND all other B2GM :
             parse .htm file from 'Save page as' 'Webpage, HTML only' as of 20191015
             return list of name1,name2,institution

        Try to take into account that name1 or name2 can be the family name or given name

        For 35th B2GM, institution is not provided. I do not know why.

        str and unicode : https://stackoverflow.com/questions/10288016/usage-of-unicode-and-encode-functions-in-python
        '''
        debug = False

        B2GMfolks = []
        typesSeen = []
        if '.txt' in B2GMfile:
            f = open(B2GMfile,'r')
            for line in f:
                if 'Participant' not in line: # avoid header
                    j = line.find('\t')
                    name1 = line[:j].replace('\t',' ').strip()
                    name2 = line[j+1:-1].replace('\t',' ').strip()
                    B2GMfolks.append( [name1,name2] )
            f.close()
        else:
            page = parse(B2GMfile)
            buff = []
            px =  page.xpath('//tr/td//text()')
            expectedFields = 3 # first, last, institution
            if '35th' in B2GMfile : expectedFields = 2
            for i,a in  enumerate( px ):
                b = a.replace('\n','').strip()
                t = type(b)
                if t not in typesSeen: typesSeen.append(t)
                if type(b) is str: b = b.decode('utf-8') # make str unicode
                j = i%expectedFields
                if j<=expectedFields-1: buff.append(b)
                if j==expectedFields-1:
                    if expectedFields==2 : buff.append( None ) # no institution
                    B2GMfolks.append(buff)
                    buff = []

        print 'climate.readB2GM Processed',len(B2GMfolks),'participants in',B2GMfile,'with',len(typesSeen),'types of characters',typesSeen
        if debug: print B2GMfolks
        return B2GMfolks
    def readCO2(self):
        '''
        read CO2 data on r/t flights between airports from https://www.icao.int/environmental-protection/CarbonOffset/Pages/default.aspx
        col 0 = Origin airport
        col 1 = Destination
        col 2 = number of legs (1=nonstop, 2=onestop, etc.)
        col 3 = distance in km between origin and destination
        col 4 = kg of C02 for round trip
        col 5 = kg / km from columns 4, 3

        return slope,intercept for linear fits to CO2(kg) vs r/t distance(km) as a function of the number of legs
        '''
        f = open(self.CO2file,'r')
        CO2data = []
        maxkm,maxkg = 0.,0.
        for line in f:
            if 'http' not in line: # skip header
                s = line.split(',')
                origin = s[0]
                if origin!='':
                    dest   = s[1]
                    legs   = int(s[2])
                    distkm = 2.*float(s[3]) # convert to r/t distance
                    CO2kg  = float(s[4])
                    maxkm = max(maxkm,distkm)
                    maxkg = max(maxkg,CO2kg)
                    CO2data.append([legs,distkm,CO2kg,origin,dest])
        f.close()
        print 'climate.readCO2 Read',len(CO2data),'lines from',self.CO2file
        # plot kg of C02 vs r/t distance in km for 1,2 legs
        fitResults = {}
        xmi,xma = 0.,1.05*maxkm
        ymi,yma = 0.,1.05*maxkg
        Xall,Yall = [],[]
        dataAndFit = {}
        for L in [1,2]:
            X,Y = [],[]
            for d in CO2data:
                if d[0]==L:
                    X.append(d[1]) # r/t distance
                    Y.append(d[2]) # 
            if len(X)>0:
                fitResults[L] = self.drawIt(X,Y,'r/t distance (km)','kg of CO2',str(L)+' legs',figDir=self.figdir,ylog=False,xlims=[xmi,xma],ylims=[ymi,yma],linfit=True)
                dataAndFit[L] = [X,Y,fitResults[L]]

            Xall.extend(X)
            Yall.extend(Y)
        if len(Xall)>0:
            self.drawIt(Xall,Yall,'r/t distance (km)','kg of CO2','All legs',figDir=self.figdir,ylog=False,xlims=[xmi,xma],ylims=[ymi,yma],linfit=True)

        X1,Y1,fR1 = dataAndFit[1]
        X2,Y2,fR2 = dataAndFit[2]
        self.drawBoth(X1,Y1,fR1,'1 leg', X2,Y2,fR2,'2 legs','r/t distance (km)','kg of CO2','CO2 vs round-trip distance')
            
        return fitResults
    def drawBoth(self,X1,Y1,fR1,Label1, X2,Y2,fR2,Label2, xtitle,ytitle,title, xlims=None, ylims=None ):
        '''
        draw 2 sets of data with linear fits
        '''
        plt.clf()
        plt.grid()
        plt.title(title)

        fit_fn = numpy.poly1d(fR1)
        x = [v for v in X1]
        x.extend( [v for v in X2] )
        w1 = ' slope {0:.3f} intercept {1:.1f}'.format(*fit_fn)
        plt.plot(X1,Y1,'ob',x,fit_fn(x),'-b',label=Label1+w1)

        fit_fn = numpy.poly1d(fR2)
        w2 = ' slope {0:.3f} intercept {1:.1f}'.format(*fit_fn)
        plt.plot(X2,Y2,'sr',x,fit_fn(x),'-r',label=Label2+w2)
        plt.xlabel(xtitle)
        plt.ylabel(ytitle)

        if xlims is None: xlims = [0., max(max(X1),max(X2))*1.05]
        if ylims is None: ylims = [0., max(max(Y1),max(Y2))*1.05]
        plt.xlim(xlims)
        plt.ylim(ylims)
        
        plt.legend(loc='best')
        pdf = self.figdir + 'all_legs.pdf'
        if pdf is not None:
            plt.savefig(pdf)
            print 'climate.drawBoth Wrote',pdf
        else:
            plt.show()
        return
    def drawIt(self,x,y,xtitle,ytitle,title,figDir=None,ylog=True,xlims=[200.,800.],ylims=[1.e-5,1.e-1],linfit=False):
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
        if linfit:
            slope,intercept = fit = numpy.polyfit(x,y,1)
            fit_fn = numpy.poly1d(fit)
            plt.plot(X,Y,'o',x,fit_fn(x),'--k')
            words = ' Fit slope {0:.3f} intercept {1:.3f}'.format(slope,intercept)
            plt.title(title + words)
        else:
            plt.plot(X,Y,'o')
            slope,intercept = None,None
        plt.xlabel(xtitle)
        plt.ylabel(ytitle)
        if ylog : plt.yscale('log')
        if debug: print 'climate.drawit ylog',ylog
        plt.xlim(xlims)
        plt.ylim(ylims)

            

        if debug: print 'climate.drawit figDir',figDir
        
        if figDir is not None:
            figpdf = figDir + figpdf
            plt.savefig(figpdf)
            print 'climate.drawIt wrote',figpdf
        else:
            if debug: print 'climate.drawit show',title
            plt.show()
        return slope,intercept
    def goodMatch(self,a,b,ch='',inIt=False):
        A = a.strip().replace(ch,'').lower()
        B = b.strip().replace(ch,'').lower()
        if A==B and len(A)>0: return True
        if inIt:
            if (A in B or B in A) and len(A)>0 and len(B)>0: return True
        return 
    def matchMtoI(self,Insts,Members,Parps):
        '''
        try to match participants Parps to Members and determine their institutions
        Result should be list of participants with their institutions including city, country

        Matching attempts:
        1. one of the names of the participants matches the first or last name of a member
        2. both of the names of the participants matches both names (first and last) of a member
        3. same as 2, but remove all dashes from names

        '''
        debug = 0
        TooFew,TooMany,JustRight = 0,0,0
        spacers = ['','-',' '] # single character spacers between names
        ParpToInst = [] # list of pairs (Participant, B2id)
        for P in Parps:
            name1,name2,inst = self.unpackParticipants(P)
            if debug>1: print 'Search for name1',name1,'name2',name2
            Matches = [] # list of B2id of potential matches
            for B2id in Members:
                firstn,middlen,lastn,lastnpre,sname = Members[B2id]
                if debug>2: print 'climate.matchMtoI first/middle/last/pre/sname',firstn,'/',middlen,'/',lastn,'/',lastnpre,'/',sname
                if self.goodMatch(name1,lastn):
                    Matches.append(B2id)
                if self.goodMatch(name2,lastn):
                    if B2id not in Matches: Matches.append(B2id)

            if len(Matches)>1: # see if we can get a name1=firstn and name2=lastn or vice-versa
                newMatch = []
                for ch in spacers:
                    for B2id in Matches:
                        firstn,middlen,lastn,lastnpre,sname = Members[B2id]
                        for initial,final in [ [firstn,lastn], [firstn+middlen,lastn], [firstn,middlen+lastn] ]:
                            if self.goodMatch(name1,initial,ch=ch) and self.goodMatch(name2,final,ch=ch) and B2id not in newMatch: newMatch.append(B2id)
                            if self.goodMatch(name2,initial,ch=ch) and self.goodMatch(name1,final,ch=ch) and B2id not in newMatch: newMatch.append(B2id)
                    if len(newMatch)>0: Matches = newMatch
                    if len(Matches)==1: break

            if len(Matches)>1 and inst!=None: # try to match one name and institution
                for ch in spacers:
                    newMatch = []
                    if debug>1: print 'climate.matchMtoI name1/name2/inst',name1,'/',name2,'/',inst,'try to match one name and institution to resolve multi-match'.upper()
                    for B2id in Matches:
                        firstn,middlen,lastn,lastnpre,sname = Members[B2id]
                        for name in [firstn,lastn,firstn]:
                            if debug>1: print 'climate.matchMtoI B2id,name/sname',B2id,name,'/',sname
                            if self.goodMatch(name1,name,ch=ch) and (sname in inst): newMatch.append(B2id)
                            if self.goodMatch(name2,name,ch=ch) and (sname in inst): newMatch.append(B2id)
                    if len(newMatch)>0: Matches = newMatch
                    if len(Matches)==1: break
                        
            if len(Matches)==0 and inst!=None: # no matches, desperation time
                Matches = []
                if debug>1: print 'climate.matchMtoI name1/name2/inst',name1,'/',name2,'/',inst,'try to match one name and institution to resolve 0 match'.upper()
                for B2id in Members:
                    if self.desperateMatch(Members[B2id],P):
                        Matches.append(B2id)
                        if debug>1: print 'climate.matchMtoI potential match B2id,name/sname',B2id,Members[B2id]
                        
            if len(Matches)>1:
                newMatch = self.bestMatch(Matches,Members,P)
                Matches = newMatch
                        
            L = len(Matches)
            
            if L==0:   # --------------> NO MATCH
                if debug>0:
                    self.printAsUnicode([ 'climate.matchMtoI name1/name2/inst',name1,'/',name2,'/',inst,'*** NO MATCHES *** '])
                TooFew += 1
                ParpToInst.append( [P, None] ) # no match
            elif L==1: # --------------> One match
                JustRight += 1
                B2id = Matches[0]
                sname = Members[B2id][-1]
                if debug>1: print 'climate.matchMtoI B2id',B2id,'sname',sname,'Members[B2id]',Members[B2id]
                if sname not in Insts:
                    print 'climate.matchMtoI ERROR dict Insts does not contain key',sname,'for participant',P
                ParpToInst.append( [P, Insts[sname]] )  # participant and Institution (city,country,longname,shortname)
            else:  # --------------> TOO MANY MATCHES
                if debug>-1:
                    self.printAsUnicode([ 'climate.matchMtoI',name1,'/',name2,'/',inst,L,'matches',Matches])
                    self.printMatches(Matches,Members) 
                TooMany += 1
                ParpToInst.append( [P, None] ) # too many matches
        print 'climate.matchMtoI',len(Parps),'participants,',JustRight,'single matches,',TooMany,'multi-matches,',TooFew,'No matches'
        
        if debug>1: # report participants and their institutions
            for pair in ParpToInst:
                P,Home = pair
                name1,name2,inst = self.unpackParticipants(P)
                print 'climate.matchMtoI',name1,name2,
                if Home is not None:
                    city,country,lname,sname = Home
                    print 'is from',sname,'(',lname,') in ',city,',',country
                else:
                    print 'has no identified home institution'
                
        return ParpToInst
    def printAsUnicode(self,wordList):
        '''
        given an input list, try to print it as unicode
        if that fails, ignore error and print as ascii
        '''
        #print 'climate.printAsUnicode wordList',wordList
        r = []
        for x in wordList:
            if type(x) is float or type(x) is int: x=str(x)
            if type(x) is list:
                r.append(x)
            else:
                try:
                    X = x.encode('utf-8')
                except UnicodeDecodeError:
                    X = x.decode('ascii','ignore')
                r.append( X )
        for x in r:print x,
        print ''
        return
    def printMatches(self,idList,Members):
        for i,B2id in enumerate(idList):
            firstn,middlen,lastn,lastnpre,sname = Members[B2id]
            print ' match#',i,B2id,firstn,'/',middlen,'/',lastn,'/',lastnpre,'/',sname
        return
    def bestMatch(self,Matches,Members,P):
        '''
        return best match among multiple matches, require at least 2 identifying bits of info to match
        Matches = list of B2id
        Members[B2id] = firstn,middlen,lastn,lastnpre,sname
        P = name1,name2,inst
        '''
        spacers = ['','-',' ']
        
        debug = 0
        
        name1,name2,inst = P
        inIt = {}
        newMatch = []
        storeI = {}
        for B2id in Matches:
            imatch = []
            for inIt in [False,True]:
                for x in P:
                    if x is not None:
                        for i,L in enumerate(Members[B2id]):
                            for ch in spacers:
                                if self.goodMatch(x,L,ch=ch,inIt=inIt):
                                    if i not in imatch:
                                        imatch.append(i)
                                        #print 'climate.bestMatch inIt,ch,x,L,i,imatch',inIt,ch,x,L,i,imatch
            

            if len(imatch)>1: newMatch.append(B2id)
            storeI[B2id] = imatch
                
        if len(newMatch)==0:
            pass
        else:
            wL = ['climate.bestMatch']
            wL.extend(P)
            wL.append('matched to')
            for B2id in newMatch:
                wL.extend(Members[B2id])
                if B2id!=newMatch[-1]: wL.append('or')
            if debug>0:
                self.printAsUnicode(wL)
                #print 'climate.bestMatch storeI',storeI
        return newMatch
        
    def desperateMatch(self,Member,P):
        '''
        try some desperate matching. One name of participant and one name in B2MMS iff instition somehow matches.
        Member is from B2MMS
        P is participant at a B2GM
        return True is deperate match is possible
        '''
        name1,name2,inst = self.unpackParticipants(P)
        if inst is None: return False 
        spacers = ['',' ','-']
        firstn,middlen,lastn,lastnpre,sname = Member
        for mname in Member:
            if mname!=sname and len(mname)>0:
                OK = False
                for ch in spacers:
                    for name in [name1,name2]:
                        if self.goodMatch(name1,mname,ch=ch) : OK = True
                    if OK: 
                        ilz = inst.lower().replace(' ','')
                        slz = sname.lower().replace(' ','')
                        if ilz in slz or slz in ilz: return True
        return False
    def unpackParticipants(self,P):
        '''
        return name1,name2,inst from B2GM row in P
        when inst is missing, make it None
        '''
        inst = None
        if len(P)==2: name1,name2 = P
        if len(P)==3: name1,name2,inst = P
        return name1,name2,inst
    def costB2GM(self,cityInfo,P2I,fitCO2):
        '''
        calculate total cost of B2GM in airfares and carbon dioxide
        cityInfo[city] = [fare, distance, comments, alternate city name] where comments = nonstop or one-stop
        P2I is list of pairs [Participant, InstInfo] 
        where Participant = name in B2GM list and InstInfo = [city,country,longname,shortname] 
        if no institution was identified, then InstInfo = None
        fitCO2[leg] = [slope,intercept] for kg of CO2 vs r/t km 
        '''
        #print '\n'
        debug = 0
        good,bad,unk,japan = 0,0,0,0
        totFares,totCarbon,totkm = 0,0,0
        for P,I in P2I:
            info = None
            if I is None:
                bad += 1
            else:
                name1,name2,inst = self.unpackParticipants(P)
                city,country,lname,sname = I
                if debug>0: print 'climate.costB2GM city/country/sname',city,'/',country,'/',sname
                if 'Japan' in country or 'Japan' in city:
                    japan += 1
                    if debug>0: print 'climate.costB2GM -----> no airfare for Japanese city'
                else:
                    found = False
                    if city in cityInfo:
                        info = cityInfo[city]
                        found = True
                    else:
                        nearby = self.nearbyCity(city,country,sname)
                        if nearby is None:
                            for c1 in cityInfo:
                                acity = cityInfo[c1][3]
                                if self.goodMatch(city,acity):
                                    info = cityInfo[c1]
                                    found = True
                                    break
                        else:
                            if nearby in cityInfo:
                                info = cityInfo[nearby]
                                found = True
                    if not found:
                        unk += 1
                        print 'climate.costB2GM Could not find',city,'/',country,'/',sname,'in cityInfo. Make sure it is in self.Airfarefile'
                    else:
                        good += 1
                        totFares += info[0]
                        distance = info[1]
                        legs = self.getLegs(info[2])
                        if debug>1: print 'climate.costB2GM P',P,'I',I,'info',info,'legs',legs
                        if legs>max(fitCO2.keys()) :
                            print 'climate.costB2GM WARNING No fit for legs',legs,'use fit for legs',max(fitCO2.keys())
                            legs = max(fitCO2.keys())
                        slope,intercept = fitCO2[legs]
                        carbon = slope*2.*distance + intercept
                        totCarbon += carbon
                        totkm += 2.*distance # round-trip distance
        print 'climate.costB2GM',len(P2I),'participants, cost of',good,'participants is',totFares,'USD',\
          totCarbon,'kg CO2 for',totkm,'km flown. Japanese/no city/inst for',japan,'/',unk,'/',bad,'participants'
        # estimate cost of participants with no home from average of good participants
        sf = 1.+float(bad)/float(good)
        c = sf*totFares 
        c2= sf*totCarbon
        km= sf*totkm
        gl = km/(2.*math.pi*self.earthRadius)
        em = km/(2.*self.earthToMoon)
        print 'climate.costB2GM Estimated total cost of {0:.2f} USD and {1:.2f} kg CO2 for {2:.1f} km flown ({3:.1f} trips around earth or {4:.1f} r/t to moon)'.format(c,c2,km,gl,em)

        totalPs = len(P2I)   # total B2GM participants
        japanPs = japan      # Japanese
        unkPs   = unk        # Unknown (could not associate institution with participant)
        badPs   = bad        # No info for institution
        estTotFares = c      # estimated total airfares, scaled to account for bad institution information
        estTotCarbon= c2     # estimated total CO2
        estTotkm    = km     # estimated total r/t distance

        Results = [totalPs, japanPs, unkPs, badPs,  totFares,totCarbon,totkm, estTotFares,estTotCarbon,estTotkm]
        
        return Results
    def getCityInfo(self,inst,city,country,cityInfo):
        '''
        return info for inst,city,country if possible, otherwise return None
        given city name and dict cityInfo 
        cityInfo is cityInfo[city1] = [fare,distance,comments,alternate name of city1]
        '''
        if city in cityInfo:
            return cityInfo[city]
        else:
            nearby = self.nearbyCity(city,country,inst)
            if nearby is None:
                for c1 in cityInfo:
                    acity = cityInfo[c1][3]
                    if self.goodMatch(city,acity):
                        return cityInfo[c1]
            else:
                if nearby in cityInfo:
                    return cityInfo[nearby]
        return None
            
    def costShifts(self,cityInfo, fitCO2, B2Inst,shiftInfo):
        '''
        estimate cost (USD), CO2 (kg), r/t distance (km) for shifters
        Inputs: 
        cityInfo is cityInfo[city1] = [fare,distance,comments,alternate name of city1]
        fitCO2[legs] = [slope,intercept]
        B2inst is dict[short name] = [city,country,long name, short name]
        shiftInfo[email] = [ inst, name, contiguous_shift_ranges]
        where contiguous_shift_ranges = [ [firstday1,lastday1], [firstday2,lastday2], ...]

        return shiftTable = [total#, japan#, unk#, bad#, minUSD, minkg, minkm, maxUSD, maxkg, maxkm]

        '''
        debug = 1
        
        tot = len(shiftInfo)
        japan,unk,bad = 0,0,0
        totFare,totCarbon,totDist = [0,0], [0,0], [0,0] #= [min,max]
        for email in shiftInfo:
            inst,name,contig = shiftInfo[email]


            if inst in B2Inst:
                city,country,lname,sname = B2Inst[inst]
                if self.goodMatch(country,'Japan') or self.goodMatch(city,'Japan'):
                    japan += 1
                else:
                    stuff = self.getCityInfo(inst,city,country,cityInfo)
                    if stuff is None:
                        if debug>0: print 'climate.costShifts Unknown inst/city/country',inst+'/'+city+'/'+country,'for email/name',email+'/'+name
                        unk += 1
                    else:
                        fare,distance,comments,acity = stuff
                        legs = self.getLegs(comments)
                        slope,intercept = fitCO2[legs]
                        carbon = slope*2.*distance + intercept
                        shiftBlocks = len(contig) 
                        for i in [0,1]:
                            sf = 1 + float(i)*float(shiftBlocks)
                            totCarbon[i] += carbon*sf
                            totDist[i] += 2.*distance*sf # round-trip distance
                            totFare[i] += fare*sf
            else:
                bad += 1
                if debug>0: print 'climate.costShifts Bad inst/name/email',inst+'/'+name+'/'+email,'inst not in Belle II institutions',"inst.replace(' ','')",inst.replace(' ','')
        shiftTable = [tot, japan, unk, bad, totFare[0], totCarbon[0], totDist[0], totFare[1], totCarbon[1], totDist[1]]
                    
        return shiftTable
    def drawResults(self,Table,kind='B2GM',column_labels=None,group=True):
        '''
        example from https://matplotlib.org/examples/ticks_and_spines/ticklabels_demo_rotation.html

        group = True = group data by Collection keys
        group = False = plot each x,y pair by itself
        '''
        
        extra = ['CDATA/Shiftmanagement_', '.htm',  'igator', 'tain']

        plt.clf()
        plt.cla()
        
        ix= 0
        x = [] # file
        xlabel = [] # terse name
        Y = {} # key is column number
        Collections = {}
        keys = ['Participants','Shifters','Fares','CO2','r/t']
        for key in keys: Collections[key] = []
        
        for fn in sorted(Table):
            tn = fn
            if kind=='B2GM'   : tn = fn[:9]
            if kind=='Shifts' :
                for g in extra: tn = tn.replace(g,'')
            ix += 1
            x.append(ix)
            xlabel.append(tn)
            columns = Table[fn]
            for icol,c in enumerate(columns):
                if icol not in Y:
                    Y[icol] = []
                if type(c) is not str:
                    Y[icol].append(c)
        #print 'climate.drawResults',        [[a,b] for a,b in zip(x,xlabel)]
        
        for icol in sorted(Y):
            y = Y[icol]
            if len(x)==len(y):
                if column_labels is not None:
                    cl = column_labels[icol]
                    for key in keys:
                        if key in cl : Collections[key].append( [x,y,cl] ) # x,y,legend
                if not group:
                    plt.plot(x, y, 'ro')
                    plt.grid()
                    dx = abs(x[1]-x[0])
                    plt.gca().set_xlim([min(x)-dx,max(x)+dx])
                    plt.gca().set_ylim([0., max(0.1,1.05*max(y))])
                    if column_labels is None:
                        plt.title('Column #'+str(icol))
                    else:
                        plt.title(column_labels[icol])
                    plt.xticks(x, xlabel, rotation=45,ha='right') #'vertical')
                    plt.grid()
                    plt.margins(0.1) #pad margins so markers don't get clipped by axes
                    plt.subplots_adjust(bottom=0.15) # tweak to prevent clipping of tick-labels
                    plt.show()

        
        symbol = ['bo','gv','r^','cs','mX','yD','k<','b>']
        if group:
            for key in keys:
                plt.clf()
                plt.cla()
                if len(Collections[key])>0:
                    yma = -1.
                    for i,trip in enumerate(Collections[key]):
                        x,y,cl = trip
                        plt.plot(x,y,symbol[i],label=cl)
                        yma = max(yma,max(y))
                    plt.legend(loc='best')
                    plt.gca().set_ylim([0.,yma*1.05])
                    plt.xticks(x,xlabel,rotation=45,ha='right')
                    plt.margins(0.1)
                    plt.grid()
                    plt.subplots_adjust(bottom=0.15)
                    figpdf = kind + '_' + key.replace('/','-') + '.pdf'
                    figpdf = self.figdir + figpdf
                    plt.savefig(figpdf)
                    print 'climate.drawResults wrote',figpdf

 #                   plt.show()

        return
    def printResults(self,Table,kind='B2GM'):
        '''
        print results contained in Table
        Table[B2GM filename prefix] = Results (list defined in costB2GM)
        '''
        latexFile = self.figdir + kind + '_table.tex'
        latex = open(latexFile,'w')

        ds = ' \\\\ \n' # print ds =>   ' \\'

        comment,latexComment = {},{}
        comment['B2GM'] = '#att = Number of attendees, japn = Number of attendees from Japan, unk = could not associate institution with attendee, bad = attendee not in B2MMS'
        comment['Shifts'] = '#att = Number of shifters, japn = Number of shifters from Japan, unk = could not associate institution with shifter, bad = shifter with unknown institution'
        latexComment['B2GM'] = 'att = Number of attendees, japn = Number of attendees from Japan, unk = could not associate institution with attendee, bad = attendee not in B2MMS. Latter case can arise if name of individual could not be unambiguously or easily matched to a B2MMS entry.'
        latexComment['Shifts'] = 'att = Number of shifters, japn = Number of shifters from Japan, unk = could not associate institution with shifter, bad = shifter with unknown institution. Latter cases can arise if individual is not in B2MMS or name of individual could not be unambiguously or easily matched to a B2MMS entry.'

        

        label = 'tab:'+kind
        caption = kind + ' statistics. ' + latexComment[kind]
        latex.write('\\begin{table}[htp] \n')
        latex.write( '\\setlength{\\tabcolsep}{2pt} \n')
        latex.write('\\begin{center} \n')
        latex.write('\\begin{tabular}{|rrrr| rrr| rrr| c|} \n' )
        
        fmt = '{0:>4} {1:>4} {2:>4} {3:>4} {4:>10.0f} {5:>10.0f} {6:>10.0f} {7:>10.0f} {8:>10.0f} {9:>10.0f} {10}'
        fmtLatex = fmt.replace('} {','}&{') + ds
        tfmt = fmt.replace('.0f','')
        tfmtLatex = tfmt.replace('} {','}&{') + ds
        hfmt = '\n{0:^19} {1:^31} {2:^31}'
        hfmtLatex = '\multicolumn(4)(|c|)({0}) & \multicolumn(3)(c|)({1}) & \multicolumn(3)(c|)({2}) &'
        latex.write( '\\hline \n' )
        if kind=='B2GM':
            print hfmt.format('Participants','Actual totals','Estimated totals')
            latex.write( hfmtLatex.format('Participants','Actual totals','Estimated totals').replace('(','{').replace(')','}') + ds )
        if kind=='Shifts':
            print hfmt.format('Participants','Est. minimum totals','Est. maximum totals')
            latex.write( hfmtLatex.format('Participants','Est. minimum totals','Est. maximum totals').replace('(','{').replace(')','}') +ds )
        column_labels = {}
        column_labels['B2GM'] = ['Participants\ Total','Participants\  from Japan','Participants\ Unknown inst','Participants\ Bad entry',\
                                'Actual total\ Fares(USD)','Actual total\ CO2(kg)','Actual total\ r/t (km)',\
                                'Estimated total\ Fares(USD)','Estimated total\ CO2(kg)','Estimated total\ r/t (km)'
                                ]
        column_labels['Shifts'] = ['Shifters\ Total','Shifters\  from Japan','Shifters\ Unknown inst','Shifters\ Bad entry',\
                                'Minimum total\ Fares(USD)','Minimum total\ CO2(kg)','Minimum total\ r/t (km)',\
                                'Maximum total\ Fares(USD)','Maximum total\ CO2(kg)','Maximum total\ r/t (km)'
                                ]
                             
        print tfmt.format('#att','japn','unk','bad', 'fares(USD)','CO2(kg)','r/t (km)', 'Fare(USD)','CO2(kg)','r/t (km)','Event')
        latex.write( tfmtLatex.format('att','japn','unk','bad', 'fares(USD)','CO2(kg)','r/t (km)', 'Fare(USD)','CO2(kg)','r/t (km)','Event') )
        latex.write( '\\hline \n' )
        s = []
        for B2GMfn in sorted(Table):
            r = Table[B2GMfn]
            if len(s)==0:
                s = [x for x in r]
            else:
                s = [x+y for x,y in zip(r,s)]
            if kind=='Shifts':
                tB2GM = B2GMfn.replace('CDATA/Shiftmanagement_','').replace('_',' ').replace('.htm','')
            elif kind=='B2GM':
                tB2GM = B2GMfn[:B2GMfn.index('B2GM')+4].replace('_',' ')
            r.append(tB2GM)
            print fmt.format(*r)
            latex.write( fmtLatex.format(*r) )
        s.append('SUMMED')
        print fmt.format(*s)
        l = len(Table)
        u = [int(x/float(l)+0.5) for x in s[:-1]]
        u.append('AVERAGE')
        print fmt.format(*u)
        print comment[kind]
        
        latex.write( '\\hline \n' )
        latex.write('\\end{tabular} \n')
        latex.write('\\label{'+label+'} \n')
        latex.write('\\caption{'+caption+'} \n')
        latex.write('\\end{center} \n')
        latex.write('\\end{table} \n') 

            
        latex.close()
        print 'climate.printResults Wrote',latexFile
        return column_labels
    def nearbyCity(self,city,country,sname):
        '''
        figure out nearby cities
        '''
        # based on Oct 2019 B2GM
        if self.goodMatch(city,'Italy'): return 'Rome'
        if self.goodMatch(country,'Italy'): return 'Rome'
        if self.goodMatch(country,'Germany'): return 'Frankfurt'
        if self.goodMatch(sname,'BNL') : return 'New York'
        if self.goodMatch(sname,'VPI') : return 'Washington'
        if self.goodMatch(sname,'Mississippi') : return 'Memphis'
        if self.goodMatch(city,'Austria') : return 'Vienna'
        if self.goodMatch(country,'Austria') : return 'Vienna'
        if self.goodMatch(sname,'Pittsburgh') : return 'Pittsburgh'
        if self.goodMatch(sname,'McGill') : return 'Montreal'
        if self.goodMatch(sname,'Victoria') : return 'Vancouver'
        if self.goodMatch(country,'France') : return 'Paris'
        if self.goodMatch(sname,'Luther') : return 'Chicago'
        if self.goodMatch(city,'Mexico') or self.goodMatch(country,'Mexico') : return 'Mexico City'
        if self.goodMatch(country,'South Korea') : return 'Seoul'
        if 'Taipei' in city: return 'Taipei'
        if self.goodMatch(sname,'Fudan') : return 'Shanghai'
        if self.goodMatch(country,'Spain') : return 'Madrid'
        if self.goodMatch(sname,'Duke') : return 'Charlotte'

        # based on June 2019 B2GM
        if self.goodMatch(sname,'MIPT') : return 'Moscow'
        if self.goodMatch(sname,'CPPM') : return 'Marseille'
        if self.goodMatch(city,'Taiwan'): return 'Taipei'
        if self.goodMatch(country,'Thailand') : return 'Bangkok'
        if self.goodMatch(sname,'Soochow') : return 'Shanghai'
        if self.goodMatch(sname,'Florida') : return 'Jacksonville'
        if self.goodMatch(sname,'IISER') : return 'Punjab'

        # based on Oct 2018 B2GM
        if self.goodMatch(sname,'Peking') : return 'Beijing'
        # based on some early B2GM
        if 'Quebec' in city: return 'Quebec'
        return None
    def getLegs(self,comments):
        '''
        determine number of legs of journey
        nonstop = 1 leg
        one stop= 2 legs
        '''
        cl = comments.lower()
        Legs = self.Legs
        for L in Legs:
            for w in Legs[L]:
                if w in cl: return L
        sys.exit('climate.getLegs ERROR '+comments)
        return None
    def mainAirFares(self):
        '''
        main routine to figure out total of airfares for B2GM

        First get airport data, then airfares between city pairs (2d city is always Tokyo),
        then compute distances and fare/km

        produce dicts
        cityIATA[city1] = [IATA, Latitude, Longitude]
        cityInfo[city1] = [fare,distance,comments,alternate name of city1]

        '''
        GAD = self.getGAD()
        AirFares = self.readAirFares()
        cityIATA = {}
        cityInfo = {}
        Nfare,avcpkm,mincpkm,maxcpkm,rms = 0, 0., 1.e20, -1.e20, 0.
        distances,fares = [],[]
        debug = 0
        for city1 in AirFares:
            fare = AirFares[city1][0]
            city2= AirFares[city1][2]
            acity1= AirFares[city1][3] # alternate name of city1
            comments= AirFares[city1][4] # comments (nonstop or onestop)
            debug,country = 0,None
            IATA = ct.findIATA(GAD,city1,country=country,debug=debug)
            if IATA is None: IATA = ct.findIATA(GAD,acity1,country=country,debug=debug)
            if IATA is None:
                if debug>0: print 'climate.mainAirFares try to match city1',city1,'by hand'
                if self.goodMatch(city1,'Novosibirsk') :
                    IATA = 'OVB'
                    if IATA=='OVB': latitude, longitude = 55.0411111, 82.9344444 # Novosibirsk from travel math.com
                    cityIATA[city1] = [IATA,latitude,longitude]
                elif self.goodMatch(city1,'Jinan') or self.goodMatch(acity1,'Jinan'):
                    IATA = 'TNA'
                    latitude, longitude = 36.66833, 116.99722
                    cityIATA[city1] = [IATA, latitude,longitude] # Jinan from latitudelongitude.org
                elif self.goodMatch(city1,'Punjab'):
                    IATA = 'AIP'
                    latitude, longitude = 31.379999, 75.379997
                    cityIATA[city1] = [IATA, latitude,longitude] # Punjab from https://www.latlong.net/place/kapurthala-punjab-india-11411.html
                elif self.goodMatch(city1,'Chiang Mai'):
                    IATA = 'CNX'
                    latitude, longitude = 18.79038, 98.98468
                    cityIATA[city1] = [IATA, latitude,longitude]
                elif self.goodMatch(city1,'Richland'):
                    IATA = 'PSC'
                    latitude, longitude = 46.28569, -119.28446
                    cityIATA[city1] = [IATA, latitude,longitude]
                elif self.goodMatch(city1,'Liaoning'): #
                    IATA = 'SHE'
                    latitude, longitude = 41.79222, 123.43278
                    cityIATA[city1] = [IATA, latitude,longitude]
                elif self.goodMatch(city1,'Guwahati'):
                    IATA = 'GAU'
                    latitude,longitude = 26.183333, 91.733333
                    cityIATA[city1] = [IATA, latitude,longitude] # from https://www.travelmath.com/cities/Guwahati,+India
                elif self.goodMatch(city1,'Shenyang') or self.goodMatch(acity1,'Shenyang'):
                    IATA = 'SHE'
                    latitude,longitude = 41.835441, 123.42944 # https://www.findlatitudeandlongitude.com/?loc=Liaoning
                    cityIATA[city1] = [IATA, latitude,longitude]
                else:
                    sys.exit('climate.mainAirFares ERROR No IATA for '+city1)
            else:
                cityIATA[city1] = [IATA,float(GAD[IATA][14]),float(GAD[IATA][15])] # IATA, Latitude, Longitude
                
            if city2 not in cityIATA: # find city2 in database
                IATA = ct.findIATA(GAD,city2)
                if IATA is None:
                    sys.exit('climate.mainAirFares ERROR No IATA for '+city2)
                else:
                    cityIATA[city2] = [IATA,float(GAD[IATA][14]),float(GAD[IATA][15])]
            p1 = cityIATA[city1][1:]
            p2 = cityIATA[city2][1:]
            distance = self.haversine(p1,p2)
            cityInfo[city1] = [fare,distance,comments,acity1]
            fares.append(fare)
            distances.append(distance)
            cpkm = None
            if distance>0:cpkm = fare/distance
            Nfare += 1
            avcpkm += cpkm
            rms += cpkm*cpkm
            maxcpkm = max(maxcpkm,cpkm)
            mincpkm = min(mincpkm,cpkm)
            if debug>0: print 'self.mainAirFares',city1,city2,'Fare(USD)',fare,'distance(km)',distance,'USD/km',cpkm
        avcpkm = avcpkm/float(Nfare)
        rms = math.sqrt( float(Nfare)/float(Nfare-1) * (rms/float(Nfare) - avcpkm*avcpkm) )
        print 'climate.mainAirFares # {0} fares with average {1:.3f}({2:.3f}) minimum {3:.3f} maximum {4:.3f} in USD/km'.format(Nfare,avcpkm,rms,mincpkm,maxcpkm)

        if debug>0:
            print '\ncityInfo: city1/fare/distance/comments/acity1'
            for city1 in sorted(cityInfo):
                fare,distance,comments,acity1 = cityInfo[city1]
                print '{0}/{1:.0f}/{2:.0f}/{3}/{4}'.format(city1,fare,distance,comments,acity1) 
            print '\n'

        
        B2Inst = self.readB2I(debug=0)
        B2Members,B2MemberEmail = self.readB2M()
        fitCO2 = self.readCO2()
        print '\n -------------------------'

        processB2GM  = True
        processShifts= True

        if processB2GM: 
            Table = {}
            for B2GMfile in self.B2GMfiles:
                B2GMfolks = self.readB2GM(B2GMfile)
                P2I = self.matchMtoI(B2Inst,B2Members,B2GMfolks)

                Results = self.costB2GM(cityInfo,P2I,fitCO2)
                fn = os.path.basename(B2GMfile).split('.')[0]
                Table[fn] = Results
            column_labels = self.printResults(Table)
            self.drawResults(Table,kind='B2GM',column_labels=column_labels['B2GM'])
        else:
            print 'climate.mainAirFares DID NOT PROCESS B2GM files'

        if processShifts: #### PROCESS SHIFT INFORMATION
            pairs = []
            fn = self.b2parser.getNextShiftFile()
            while (fn is not None):
                shiftInfo = self.b2parser.readShift(fn)
                pairs.append( [fn, shiftInfo] )
                fn = self.b2parser.getNextShiftFile()
            shiftTable = {}
            for pair in pairs:
                fn,shiftInfo = pair
                shiftTable[fn] = ShiftResults = self.costShifts(cityInfo,fitCO2, B2Inst,shiftInfo)
            column_labels = self.printResults(shiftTable,kind='Shifts')
            self.drawResults(shiftTable,kind='Shifts',column_labels=column_labels['Shifts'])
        else:
            print 'climate.mainAirFares DID NOT PROCESS SHIFT INFORMATION' 
        
        if 0: 
            self.drawIt(distances,fares,'Distance between city and Tokyo in km','Fare(USD)','Cost per km',figDir=None,ylog=False,xlims=[0.,14000.],ylims=[0.,2400.])
        
        return
if __name__ == '__main__' :
   
    ct = climate()
    MLB = False
    if MLB:
        ct.getTeamPosition()
        ct.reDistribute()
    else:
        ct.mainAirFares()
            
#    ct.test()
