import nltk
from nltk import FreqDist, word_tokenize
from nltk.corpus import stopwords
from nltk.collocations import BigramCollocationFinder,TrigramCollocationFinder
from nltk.metrics import BigramAssocMeasures,TrigramAssocMeasures
from nltk.chunk import RegexpParser
import csv
from pprint import pprint

csvwrite = file('db\cyttron-keywords.csv', 'wb')
keywordList = []
bigramList = []
trigramList = []

#Extract wordFreq,bi/tri-grams. Store them in CSV
def extractKeywords(list):
    csv = open('db\cyttron-keywords.csv','a')
    csv.write('"keywords";"bigrams";"trigrams"\n')
    csv.close()
    for i in range(len(list)):
        currentEntry = str(list[i])
        freqWords(currentEntry,10,i)
        wordCollo(list[i])

def descKeywords(list):
    for i in range(len(list)):
        currentEntry = str(list[i][0])
        print currentEntry
        freqWords(currentEntry,25)
        wordCollo(currentEntry)
        print " "
    
def freqNouns(string,int):
    list=[]
    words = nltk.word_tokenize(string)
    pos = nltk.pos_tag(words)
    for i in range(len(pos)):
        if len(pos[i][0]) > 1:
            if pos[i][1] == 'NN' or pos[i][1] == 'NNP':
                list.append(pos[i][0])
    newString = ' '.join(list)
    freqWords(newString,int)

def freqWords(string,int):
    global pub
    wordList=[]
    stopset = set(stopwords.words('english'))
    words = nltk.word_tokenize(string)
    wordsCleaned = [word.lower() for word in words if word.lower() not in stopset and len(word) > 2]
    fdist = FreqDist(wordsCleaned).keys()
    if len(wordsCleaned) < int:
        int = len(wordsCleaned)-1
    if int > 0:
        for j in range(1,int):
            word = fdist[j-1:j]
            wordList.append(str(word[0]))
    csv = open('db\cyttron-keywords.csv','a')
    if len(wordList) > 1:
        csv.write('"' + ', '.join(wordList[:-1]) + ', ' + wordList[-1] + '";')
    else:
        csv.write('"' + ''.join(wordList) + '";')
    print wordList
    csv.close()

def wordCollo(string):
    biList=[]
    triList=[]
    words = nltk.word_tokenize(string)
    stopset = set(stopwords.words('english'))
    words = [word.lower() for word in words if word.lower() not in stopset and len(word) > 2]
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
    if len(biList) > 1:
        csv.write('"' + ', '.join(biList[:-1]) + ', ' + biList[-1] + '";')
    else:
        csv.write('"' + ''.join(biList) + '";')
    csv.close()
    print biList
    
    for i in range(len(triResult)):
        if len(triResult) > 0:
            triPrint = " ".join(triResult[i])
            triList.append(triPrint)
        else:
            triList=[]
    csv = open('db\cyttron-keywords.csv','a')
    if len(triList) > 1:
        csv.write('"' + ', '.join(triList[:-1]) + ', ' + triList[-1] + '"\n')
    else:
        csv.write('"' + ''.join(triList) + '"\n')
    csv.close()
    print triList

def readResults():
    global keywordList,bigramList,trigramList
    results = csv.reader(open('db\cyttron-keywords.csv', 'rb'), delimiter=';')
    for line in results:
        if len(line[0])>0:
            keywordList.append(line[0])
        if len(line[1])>0:
            bigramList.append(line[1])
        if len(line[2])>0:
            trigramList.append(line[2])
