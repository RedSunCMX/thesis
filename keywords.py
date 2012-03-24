import nltk
from nltk import FreqDist, WordPunctTokenizer
from nltk.corpus import stopwords
from nltk.collocations import BigramCollocationFinder,TrigramCollocationFinder
from nltk.metrics import BigramAssocMeasures,TrigramAssocMeasures
from nltk.chunk import RegexpParser
import csv
from pprint import pprint
from nltk import TextCollection

csvwrite = file('db\cyttron-keywords.csv', 'wb')
bigramList = []
trigramList = []
wordList = []

# Extract wordFreq,bi/tri-grams. Store them in CSV
def extractKeywords(selection,corpus,nr):
    csv = open('db\cyttron-keywords.csv','w')
    cyttronCorpus = TextCollection(corpus)
    for i in range(len(selection)):
        currentEntry = selection[i].lower()
        freqWords(currentEntry,cyttronCorpus,nr)
        freqNouns(currentEntry,cyttronCorpus,nr)
        nGrams(currentEntry,cyttronCorpus,nr,clean=True)
    csv.close()

def freqWords(string,corpus,number):
    global pub,wordList
    wordList=[]
    stopset = set(stopwords.words('english'))
    words = WordPunctTokenizer().tokenize(string)
    wordsCleaned = [word.lower() for word in words if word.lower() not in stopset and len(word) > 2 ]
    for i in range(len(wordsCleaned)):
        wordList.append((corpus.tf_idf(wordsCleaned[i],string),wordsCleaned[i]))
    wordList = list(set(wordList))
    wordList = sorted(wordList,reverse=True)
    final = [word[1] for word in wordList[:number]]
    csv = open('db\cyttron-keywords.csv','a')
    if len(final) > 1:
        csv.write('"' + ','.join(final[:-1]) + ',' + final[-1] + '";')
    else:
        csv.write('"' + ''.join(final) + '";')
    csv.close()
    return final

# String-functions
def freqNouns(string,corpus,number):
    list=[]
    words = WordPunctTokenizer().tokenize(string)
    pos = nltk.pos_tag(words)
    for i in range(len(pos)):
        if len(pos[i][0]) > 1:
            if pos[i][1] == 'NN' or pos[i][1] == 'NNP':
                list.append(pos[i][0])
    newString = ' '.join(list).lower()
    freqWords(newString,corpus,number)

def nGrams(string,corpus,number,clean=True):
    global wordList
    biList=[]
    triList=[]
    words = WordPunctTokenizer().tokenize(string)
    stopset = set(stopwords.words('english'))
    if clean == True:
        words = [word.lower() for word in words]
    if clean == False:
        words = [word.lower() for word in words]
    filter = lambda words: len(words) < 2 or words.isdigit()
    
    bcf = BigramCollocationFinder.from_words(words)
    bcf.apply_word_filter(filter)
    biResult = bcf.nbest(BigramAssocMeasures.likelihood_ratio, number)

    tcf = TrigramCollocationFinder.from_words(words)
    tcf.apply_word_filter(filter)
    triResult = tcf.nbest(TrigramAssocMeasures.likelihood_ratio, number)

    for i in range(len(biResult)):
        if len(biResult) > 0:
            biPrint = " ".join(biResult[i])
            biList.append(biPrint)
        else:
            biList=[]
    csv = open('db\cyttron-keywords.csv','a')            
    if len(biList) > 1:
        csv.write('"' + ','.join(biList[:-1]) + ',' + biList[-1] + '";')
    else:
        csv.write('"' + ''.join(biList) + '";')
    csv.close()
    
    for i in range(len(triResult)):
        if len(triResult) > 0:
            triPrint = " ".join(triResult[i])
            triList.append(triPrint)
        else:
            triList=[]
    csv = open('db\cyttron-keywords.csv','a')
    if len(triList) > 1:
        csv.write('"' + ','.join(triList[:-1]) + ',' + triList[-1] + '"\n')
    else:
        csv.write('"' + ''.join(triList) + '"\n')
    csv.close()
    print biList
    print triList
