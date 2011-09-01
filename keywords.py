import nltk
from nltk import FreqDist, word_tokenize
from nltk.corpus import stopwords
from nltk.collocations import BigramCollocationFinder,TrigramCollocationFinder
from nltk.metrics import BigramAssocMeasures,TrigramAssocMeasures
from nltk.chunk import RegexpParser
import csv

csvwrite = file('db\cyttron-keywords.csv', 'wb')
keywordList = []
bigramList = []
trigramList = []

#Exctract wordFreq,bi/tri-grams. Store them in CSV
def extractKeywords(list):
    csv = open('db\cyttron-keywords.csv','a')
    csv.write('"keywords";"bigrams";"trigrams"\n')
    csv.close()
    for i in range(len(list)):
        currentEntry = str(list[i])
        freqWords(currentEntry,10,i)
        wordCollo(list[i])

def freqWords(string,int,line):
    global pub
    wordList=[]
    stopset = set(stopwords.words('english'))
    words = nltk.word_tokenize(string)
    wordsCleaned = [word.lower() for word in words if word.lower() not in stopset and len(word) > 2]
    # print "\nWords:",len(words),"\t",
    # print "Cleaned:",len(wordsCleaned)
    # print "\n",line
    # print "Keywords:",
    fdist = FreqDist(wordsCleaned).keys()
    if len(wordsCleaned) < int:
        int = len(wordsCleaned)-1
        print "too few words, trying",int,
    if int > 0:
        for j in range(1,int):
            word = fdist[j-1:j]
            wordList.append(str(word[0]))
    csv = open('db\cyttron-keywords.csv','a')
    csv.write('"' + str(wordList) + '";')
    csv.close()
    
def wordCollo(string):
    biList=[]
    triList=[]
    words = nltk.word_tokenize(string)
    filter = lambda words: len(words) < 2 or words.isdigit()
    
    bcf = BigramCollocationFinder.from_words(words)
    bcf.apply_word_filter(filter)
    biResult = bcf.nbest(BigramAssocMeasures.likelihood_ratio, 10)

    tcf = TrigramCollocationFinder.from_words(words)
    tcf.apply_word_filter(filter)
    triResult = tcf.nbest(TrigramAssocMeasures.likelihood_ratio, 4)

    for i in range(len(biResult)):
        if len(biResult) > 0:
            biPrint = " ".join(biResult[i])
            biList.append(biPrint)
        else:
            biList=[]
    csv = open('db\cyttron-keywords.csv','a')            
    csv.write('"' + str(biList) + '";')
    csv.close()
    
    for i in range(len(triResult)):
        if len(triResult) > 0:
            triPrint = " ".join(triResult[i])
            triList.append(triPrint)
        else:
            triList=[]
    csv = open('db\cyttron-keywords.csv','a')
    csv.write('"' + str(triList) + '"\n')
    csv.close()

def readResults():
    global keywordList,bigramList,trigramList
    results = csv.reader(open('db\cyttron-keywords.csv', 'rb'), delimiter=';')
    for line in results:
        if len(line[0])>0:
            print line[0],
            keywordList.append(line[0])
        if len(line[1])>0:
            print line[1],
            bigramList.append(line[1])
        if len(line[2])>0:
            print line[2]
            trigramList.append(line[2])
