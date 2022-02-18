#!/usr/bin/env python
'''
use RAKE to try to extract key words and phrases

20220218
'''
import sys,os
from rake_nltk import Rake
import re

class robot():
    def __init__(self,debug=0):
        
        self.debug = debug

        self.rake = Rake()
        
        # there must be a better way to add stopwords
        s = self.rake.stopwords
        x = list(s)
        x.append('max 32')
        x.append('32')
        self.rake = Rake(x)

        
        print('robot.__init__ Completed')
        return
    def readSubjects(self, fn='all_subjects.txt'):
        '''
        return subjects read from file prepared by awk-ing logfile.log
        '''
        f = open(fn,'r')
        subjects = []
        for line in f: subjects.append( line[:-1] )
        f.close()
        print('robot.readSubjects Read',len(subjects),'subjects from file',fn)
        return subjects
    def Extract(self,Subjects):
        '''
        create  lists of words and sentences extracted from input list Subjects 
        and scoredPhrases = list of tuples (score,phrase)
        and freqWords = dict {word : freq} , freq = integer
        and degWords = dict {word : degree}, degree = integer
        (degree is how many times a word appears in a co-occurance table of word vs word, so degree >= frequency)
        '''
        text = ', '.join(Subjects)
        self.rake.extract_keywords_from_text(text)
        self.rake.extract_keywords_from_sentences(Subjects)
        
#        self.words = self.rake.word_tokenizer(text) 
#        self.sentences = self.rake.sentence_tokenizer(Subjects)
        
        self.scoredPhrases = self.rake.get_ranked_phrases_with_scores()
        # remove duplicates and preserve descending order in list
        self.scoredPhrases = sorted(list(set(self.scoredPhrases)),reverse=True) 
        self.freqWords = self.rake.get_word_frequency_distribution()
        self.degWords  = self.rake.get_word_degrees()
        return
    def show(self,n=20):
        '''
        show top n entries in thang
        '''
        fW = sorted( ((v,k) for k,v in self.freqWords.items()), reverse=True)
        dW = sorted( ((v,k) for k,v in self.degWords.items()), reverse=True)
        thangs =  [x for x in reversed([self.scoredPhrases, fW, dW])]
        tNames =  [x for x in reversed(['scoredPhrases', 'freqWords', 'degWords'])]
        for thang,tName in zip(thangs,tNames):
            #print('\nrobot.show',tName,'\n',thang,'++++++++++++++++++++\n')
            print('\nrobot.show Show top',n,'out of',len(thang),'entries in',tName)
            for i in range(n):
                score,phrase = thang[i]
                print('{:.1f} {}'.format(score,phrase))
        
        return
    def winnowPhrases(self,Subjects):
        '''
        are Phrases in Subjects or vice-versa?
        '''
        print('\nrobot.winnowPhrases')
        text = list(set(' '.join(Subjects)))
        N = len(self.scoredPhrases)
        N = 25
        for i in range(N):
            score,phrase = self.scoredPhrases[i]
            tag = ''
            if self.grep(phrase,Subjects): tag += ' IS SUBJECT'
            nWords = self.wordsInPhrase(text,phrase)
            if nWords>0 : tag += ' ' + str(nWords) + ' matched'
            print('{:.1f} {} {}'.format(score,phrase,tag))
        return
    def grep(self,phrase,sentences):
        '''
        return True if phrase is in one of the items in the list sentences
        '''
        for sentence in sentences:
            #print('robot.grep phrase',phrase,'sentence',sentence)
            match = re.search(phrase,sentence)
            if match : return True
        return False
    def wordsInPhrase(self,text,phrase):
        ''' count the number of words in list text that are in phrase '''
        nWord = 0
        for word in text:
            if word in phrase: nWord += 1
        return nWord
    def main(self):
        Subjects = self.readSubjects()
        self.Extract(Subjects)
        self.show(n=25)
        subjects = [x.lower() for x in Subjects]
        self.winnowPhrases(subjects)

        return
if __name__ == '__main__' :
    rb = robot()
    rb.main()
