#!/usr/bin/env python
'''
extract the original email text from a message from comp-users-forum

main use is extractMsg.getEmailMsg(filename) 
where filename is the file that contains one message from 
the comp-users-forum archive

20210922
'''
#import math
import sys,os
import glob
import email, base64
import numpy
import datetime


class extractMsg():
    def __init__(self,prefix='DATA/comp-users-forum',debug=0):
        self.debug = debug
        self.badKeys = {}
        self.dirPrefix = prefix

        print('extractMsg.__init__ completed')
        return
    def getMessageFromFile(self,fn):
        '''
        return message from email file named fn

        try,except needed with python3 since some messages can only be retrieved when 
        the file is opened as binary
        20211124
        '''
        f = open(fn,'r')
        try:
            msg = email.message_from_file(f)
        except UnicodeDecodeError:                  
            f.close()                               
            f = open(fn,'rb')                       
            msg = email.message_from_binary_file(f) 
        f.close()
        return msg            
    def gridSites(self,files=None):
        '''
        return list allSites containing names of all grid sites found in email
        messages in input files

        20211124 python3 mod, add try,except because of inability to decode message
        '''
        if files is None : files = glob.glob(self.dirPrefix + '_20*/*')
        #files = glob.glob(self.dirPrefix + '_2018-10/20')  # problematic file for get_text

        allSites = []
        for i,fn in enumerate(files):

            ##print('extractMsg -------------- look for grid site names in message from fn',fn)
            msg = self.getMessageFromFile(fn)

            msg = self.msgFix(msg)
            #print 'msg after msgFix\n',msg
            lines = self.get_text(msg)
            sites = self.getGridSiteNames(lines)
            for site in sites:
                if site not in allSites:
                    if self.debug > 1 : print('extractMsg.gridSites fn',fn,'site',site)
                    allSites.append(site)
        if self.debug > 2 : print('extractMsg.gridSites allSites',allSites)
        return allSites

    def getGridSiteNames(self,msg):
        '''
        let's see if the names of grid sites can be extracted from the text of email messages

        grid site name cannot contain character in list ignore
        grid site name is of the form 'first.middle.last'
        require len(last) <= tooLong
        last character in name cannot be '.'
        if first or middle or last isdigit(), then name is not valid        

        '''
        ignore = ['*',':','tar.gz','tar.bz2','stash.','http','@','/','.org','.log','www.','e.g.',
                      '(',')','<','>','__','--','\xc2','\xa0','\xe2','\x80','\x98','proc10.lfn.aa']
        tooLong = 2

        sites = []
        lines = msg
        for word in lines.split():
            if self.validSiteName(word,ignore=ignore,tooLong=tooLong) :
                if word not in sites:
                    if self.debug > 2 : print('extractMsg.getGridSiteNames word',word)
                    sites.append(word)

        sites.sort(key=len)
        if self.debug > 2 : print('extract.getGridSiteNames sites before clean',sites)
        clean = []
        delim = ['"',"'"]
        comma = ','
        for word in sites:
            newword = word
            if self.debug > 2 : print('extractMsg.getGridSiteNames word',word)
            for d in delim:
                if word.count(d)==2:
                    newword = word.split(d)[1]
                    break
                elif word.count(d)==1:
                    newword = word.replace(d,'')
                    break
            if newword==word:
                if comma in word:
                    if word.index(comma)==len(word)-1 :
                        newword = word.replace(comma,'')
                    elif word.index(comma)<len(word)-1 :
                        newword = word.split(comma)[1]
                        
            if self.validSiteName(newword,ignore=ignore,tooLong=tooLong) : clean.append( newword )
        sites = clean
        sites.sort(key=len)
        if self.debug > 2 : print('extractMsg.getGridSiteNames sites',sites)
        return sites
    def validSiteName(self,name,ignore=[],tooLong=2):
        ''' 
        return True if name is a valid grid site name 
        based on input list of bad strings 'ignore' and 
        tooLong as maximum length of last part of name
        '''
        word = name
        if type(word) is bytes : word = name.decode('utf-8') ## python3

        if len(word)<5 : return False
        if self.debug > 2 : print('extractMsg.validSiteName word',word)
        if word.count('.')!=2: return False

        if word[-1]=='.' : return False
        if len(word.split('.')[-1])>tooLong : return False
            
        for crud in ignore:
            if crud in word: return False
                
        for part in word.split('.'):
            if part.isdigit() : return False
        return True
    def bigTest(self):
        '''
        run some text extraction modules on a messages from a bunch of files

        mostly diagnostic
        '''
        files = glob.glob(self.dirPrefix + '_2021*/*')
        L,E = 0,0
        for i,fn in enumerate(files):
            lines = self.getText(fn)
            emsg  = self.decodeText(fn)
            if len(lines)==0:
                L += 1
                #print fn,'zero-length text'
            if len(emsg)==0:
                E += 1
                #print fn,'zero-length message'
            if i%100==0: print('extractMsg.bigTest processing file#',i,'text/message length',len(lines),'/',len(emsg),'fn',fn,'self.badKeys',self.badKeys)
        print('extractMsg.bigTest failed to extract text/message in',L,'/',E,'files out of a total of',len(files))
        return
    def finalTest(self):
        '''
        check that zero length message can be extracted from every file
        compile/report stats on lengths extracted for all files
        '''
        files = glob.glob('DATA/comp-users-forum_20*/*')
        print('extractMsg.finalTest will process',len(files),'files')
        L = 0
        lengths = []
        Ldict = {}
        Msgs  = {}
        for i,fn in enumerate(files):
            lines = self.getEmailMsg(fn)
            lengths.append( len(lines) )
            Ldict[fn] = len(lines)
            Msgs[fn]  = lines
            if len(lines)==0:
                L += 1
                print(fn,'zero-length text')

            if i%100==0: print('extractMsg.finalTest processing file#',i,'text length',len(lines),'fn',fn)
        print('extractMsg.finalTest failed to extract email message in',L,'files out of a total of',len(files))
        A = numpy.array(lengths)
        mean,median,std,mx = numpy.mean(A), numpy.median(A), numpy.std(A), numpy.max(A)
        print('extractMsg.finalTest message length stats: mean {:.2f} median {:.2f} stddev {:.2f} max {:.2f}'.format(mean,median,std,mx))
        nSig = 5.
        fiveSigma = mean + nSig*std
        print('extractMsg.finalTest Look at messages with length',nSig,'sigma above mean, or >',fiveSigma)
        for key in sorted(Ldict, key=Ldict.get):
            #print key,Ldict[key]

            if Ldict[key] > fiveSigma:
                print('extractMsg.finalTest fn',key,'length',Ldict[key],'msg\n',Msgs[key])
            
        return
    def getArchiveDates(self,files):
        '''
        return dict archiveDates[archive] = date as datetime object
        '''
        archiveDates = {}
        for fn in files:
            archive = fn.split('_')[1]
            dt_object = self.getDate(fn,mode='filename')
            archiveDates[archive] = dt_object
        if self.debug > 2 : print('extractMsg.getArchiveDates archiveDates',archiveDates)
        return archiveDates
    def getDate(self,FN,mode='filename'):
        '''
        Return date as datetime object given filename FN (mode='filename') 
        For mode='archive', construct filename assuming FN = archive. 
        If no date is available in message in filename, then take date from filename.
        The latter always gives a first of the month date
        '''
        mfmt = '%a, %d %b %Y %X'
        afmt = '%Y-%m'
        fn = FN
        if mode=='archive': fn = self.dirPrefix + '_' + FN

        msg = self.getMessageFromFile(fn)

        dt = msg['Date']
        if dt is None:
            archive = fn.split('_')[1][:7]
            dt_object = datetime.datetime.strptime(archive,afmt)
        else:
            dts = ' '.join([x for x in dt.split(' ')[:5]])
            dt_object = datetime.datetime.strptime(dts,mfmt)
        return dt_object
    def dateTest(self):
        '''
        test getting date from email messages using recommendation of 
        https://stackoverflow.com/questions/50187007/python-get-datetime-of-mails-gmail

        For 2017-02 to 2021-08 messages, 43 of 2165 had no date. 
        2122 had same year in message and filename, 2111 had same year and month in message and filename. 
        The 11 with year+month mismatch were near the beginning or end of month. 
        '''
        fmt = '%a, %d %b %Y %X'
        files = glob.glob('DATA/comp-users-forum_20*/*')
        noDate = 0
        yearOK, YMOK = 0,0
        for fn in files:
            archive = fn.split('_')[1][:7]
            dts_object = dt_object = self.getDate(fn)
            dta_object = datetime.datetime.strptime(archive[:7],'%Y-%m')
            cmpY = cmp(dts_object.year,dta_object.year)
            cmpM = cmp(dts_object.month,dta_object.month)
            if cmpY==0: yearOK += 1
            OK = cmpY==0 and cmpM==0
            if OK : YMOK += 1
            if not OK : print(archive,dts_object.strftime(fmt),'cmpY,cmpM',cmpY,cmpM)
        print('extractMsg.dateTest',noDate,'out of',len(files),'had no Date.',yearOK,'files had year agreement',YMOK,'had year+month agreement')
        return
        
    def getText(self,INPUT,input='file'):
        '''
        return string with best guess at email message text
        use msgFix to pick the best part of the original message

        if input=='file', then INPUT is the filename
        if input=='archive', then INPUT is the archive identifier eg., 2021-03/32

        '''
        fn = None
        if input=='file': fn = INPUT
        if input=='archive': fn = self.dirPrefix + '_' + INPUT
        if fn is None : sys.exit('extractMsg.getText ERROR Invalid input='+input)
            
        dthres = 1

        if self.debug > 0 : print('extractMsg.getText fn',fn)
        msg = self.getMessageFromFile(fn)

        msg = self.msgFix(msg)

        s = self.get_text(msg)
        
        if self.debug > dthres : print('extractMsg.getText before exit len(s),s',len(s),s)
        return s
    def listParts(self,fn):
        '''
        list info on parts of msg in fn

        diagnostic use only
        '''

        if self.debug > 0 : print('extractMsg.listParts fn',fn)
        msg = self.getMessageFromFile(fn)
        i = 0
        if msg.is_multipart():
            for part in msg.walk():
                print('part',i,'items',list(part.items()))
                i += 1
        else:
            print('not multipart')
        return
    def decodeText(self,fn):
        '''
        return decoded email message text
        may return a zero-length string if text cannot be decoded

        open input file, get the best part of the message using msgFix
        and decode it if it is base64-encoded
        '''
        dthres = 1 # overall debug threshold in this module
        

        if self.debug > 0 : print('extractMsg.decodeText fn',fn)
        msg = self.getMessageFromFile(fn)
        msg = self.msgFix(msg)
                    
        if self.debug > dthres : print('extractMsg.decodeText fixed msg',msg)
        if self.debug > dthres : print('extractMsg.decodeText msg.items()',list(msg.items()))

        plaintext, charset = False, None
        for item in list(msg.items()):
            if 'Content-Type' in item[0]:
                if 'text/plain' in item[1] : plaintext = True
            if 'Content-Transfer-Encoding' in item[0] : charset = item[1]

        if self.debug > dthres : print('extractMsg.decodeText plaintext,charset',plaintext,charset)
        s = ''
        if plaintext and charset=='base64':
            s = msg.as_string()
            if self.debug > dthres : print('extractMsg.decodeText initial s\n',s)
            while charset in s:
                k = s.index(charset) + len(charset)
                if self.debug > dthres : print('extractMsg.decodeText charset k',k)
                s = s[k:]
            extraClean = True  # try to remove header and extraneous text before base64 decoding
            if extraClean:
                cr = '\n'
                while cr in s:
                    k = s.index(cr) + len(cr)
                    l1 = len(s[:k])
                    l2 = len(s[:k].strip())
                    l3 = len(s[:k].replace(' ',''))
                    if min(l1,l2,l3)>0 and l1==l3 and l2+1==l1:
                        break
                    else:
                        s = s[k:]
                    
            if self.debug > dthres : print('extractMsg.decodeText final s\n',s)
            
            try:
                s = base64.b64decode(s)
            except:
                s = ''

            if s=='' and self.debug > dthres : print('extractMsg.decodeText base64 decode Exception')
                
        if self.debug > dthres : print('extractMsg.decodeText after base64 decoding, s\n',s)
        return s
    def msgFix(self,msg):
        '''
        return most likely part of msg to be interpreted as the actual email message
        '''
        fav = {'Content-Type' : 'text/plain'}
        if msg.is_multipart():
            for part in msg.walk():
                for item in list(part.items()):
                    for key in fav:
                        if key==item[0]:
                            if fav[key] in item[1]:
                                return part
        return msg
    def msgReducer(self,msg,QUOLEV=1):
        '''
        return msg after removing quote level > quolev
        assume input msg is string
        '''
        quolev = max(1,QUOLEV)
        quote = '>'
        lines = msg.split('\n')
        for i,line in enumerate(lines):
            if line[:quolev].count(quote)==quolev:
                break
        s = ''
        for line in lines[:i]:
            s += line+'\n'
        return s
    def getEmailMsg(self,fn):
        '''
        return email message in input file, hopefully in normal text
        '''
        msg = self.decodeText(fn)
        if len(msg)==0:
            msg = self.getText(fn)
        msg = self.msgReducer(msg)
        return msg
    def get_text(self,msg):
        '''
        this code taken verbatim from the most popular answer at
        https://stackoverflow.com/questions/4824376/parse-multi-part-email-with-sub-parts-using-python
        on 20211021

        I added idiot_html2text to do rudimentary html to text translation
        Added check on charset
        Added try/except for chardet

        20211124 python3 modification. return text as string
        '''
        text = ""
        if msg.is_multipart():
            html = None
            for part in msg.get_payload():
                if part.get_content_charset() is None:
                    try:  ### added try/except
                        charset = chardet.detect(str(part))['encoding']
                    except NameError:
                        return ""
                else:
                    charset = part.get_content_charset()
                if part.get_content_type() == 'text/plain':
                    text = str(part.get_payload(decode=True),str(charset),"ignore").encode('utf8','replace')
                if part.get_content_type() == 'text/html':
                    html = str(part.get_payload(decode=True),str(charset),"ignore").encode('utf8','replace')
            if html is None:
                return str(text.strip()) ## python3
            else:
                html = self.idiot_html2text(html) ## added
                return str(html.strip()) ## python3
        else:
            cs = msg.get_content_charset()   ## added
            if cs is None : cs = 'us-ascii'  ## added
            text = str(msg.get_payload(decode=True),cs,'ignore').encode('utf8','replace') ## altered
            return str(text.strip()) ## python3
    def idiot_html2text(self,html):
        '''
        return text given html using knucklehead's method
        '''
        boring = ['&nbsp;','<i>','<\i>']
        text = ''
        for line in html.split('\n'):
            if '<div>' in line and '</div>' in line:
                l = line[line.index('<div>')+len('<div>'):line.index('</div>')-1]
                for s in boring:
                    l = l.replace(s,'').strip()
                text += l + '\n'
        return text
            
if __name__ == '__main__' :
    eM = extractMsg()
    fn = 'DATA/comp-users-forum_2020-02/22'


    testDate = False
    if testDate :
        eM.dateTest()
        sys.exit('extractMsg testDate done')
    
    listParts = False
    if listParts:
        fn = 'DATA/comp-users-forum_2021-01/107'
        if len(sys.argv)>1 : fn = sys.argv[1]
        eM.listParts(fn)
        sys.exit('extractMsg listParts ' + fn)

    getEmailMsg =  False
    if getEmailMsg:
        fn = 'DATA/comp-users-forum_2021-01/107'
        fn = 'DATA/comp-users-forum_2021-06/27'
        fn = 'DATA/comp-users-forum_2021-05/41'
        fn = 'DATA/comp-users-forum_2018-03/22'
        msg = eM.getEmailMsg(fn)
        print('message from',fn,'\n',msg)
        sys.exit('extractMsg '+fn)

    finalTest = False
    if finalTest:
        eM.finalTest()
        sys.exit('extractMsg.finalTest completed')
    

    bigTest =  False
    if bigTest : 
        eM.bigTest()
        sys.exit('extractMsg.bigTest completed')

    decodeTest = False
    if decodeTest:
        fn = 'DATA/comp-users-forum_2020-02/5'
        if len(sys.argv)>1 : fn = sys.argv[1]
        s = eM.decodeText(fn)
        print('len(s)',len(s))
        print('s\n',s)
        sys.exit('extractMsg.decodeText '+fn)

    getArchiveText = False
    if getArchiveText:
        #fn = 'DATA/comp-users-forum_2017-06/61'
        input = 'archive'
        archive = '2020-11/25'
        archive = '2021-05/32'
        if len(sys.argv)>1 : archive = sys.argv[1]
        lines = eM.getText(archive,input=input)
        print(lines)

    betterGetText = False
    if betterGetText :
        for n in range(38,39):
#            fn = 'DATA/comp-users-forum_2021-03/'+str(n)
            fn = 'DATA/comp-users-forum_2021-02/'+str(n)
            fn = 'DATA/comp-users-forum_2017-06/1'
            print('\n\nextractMsg -------------------------------- test get_text for fn',fn)
            msg = eM.getMessageFromFile(fn)
            msg = eM.msgFix(msg)
            lines = eM.get_text(msg)
            print(lines)


    lookForGridSites = False
    if lookForGridSites :
        eM.gridSites()
