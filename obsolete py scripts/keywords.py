import nltk
from nltk import FreqDist, word_tokenize
from nltk.corpus import stopwords
from nltk.collocations import BigramCollocationFinder,TrigramCollocationFinder
from nltk.metrics import BigramAssocMeasures,TrigramAssocMeasures
from nltk.chunk import RegexpParser
import csv

log = open('keywordlog.txt','a')
csvread = csv.reader(open('db\cyttron-db.csv', 'rb'), delimiter=';')
csvwrite = file('db\cyttron-results.csv', 'wb')
pub=[]
group=[]
priv=[]

def cleanCSV(csvread):
    global pub,group,priv
    for line in csvread:
        if len(line[0]) > 0:
            pub.append(line[0])
        if len(line[1]) > 0:
            group.append(line[1])
        if len(line[2]) > 0:
            priv.append(line[2])
    total1 = len(pub)
    total2 = len(group)
    total3 = len(priv)
    pub = list(set(pub))
    group = list(set(group))
    priv = list(set(priv))
    print "Public entries:",total1,"total",len(pub),"unique"
    print "Group entries:",total2,"total",len(group),"unique"
    print "Priv entries:",total3,"total",len(priv),"unique"

def extractKeywords():
    csvwrite.write('"Cyttron DB Entry";"keywords";"bigrams";"trigrams"\n')    
    for i in range(len(pub)):
        csvwrite.write('"' + str(pub[i]) + '";')
        currentEntry = str(pub[i])
        freqWords(currentEntry,10,i)
        wordCollo(pub[i])

def freqWords(string,int,line):
    global pub
    wordList=[]
    stopset = set(stopwords.words('english'))
    words = nltk.word_tokenize(string)
    wordsCleaned = [word.lower() for word in words if word.lower() not in stopset and len(word) > 2]
    # print "\nWords:",len(words),"\t",
    # print "Cleaned:",len(wordsCleaned)
    print "\n",line
    print "Keywords:",
    fdist = FreqDist(wordsCleaned).keys()
    if len(wordsCleaned) < int:
        int = len(wordsCleaned)-1
        # print "too few words, trying",int,
    if int > 0:
        for j in range(1,int):
            word = fdist[j-1:j]
            wordList.append(str(word[0]))
    csvwrite.write('"' + str(wordList) + '";')
    
def wordCollo(string):
    biList=[]
    triList=[]
    log = open('keywordlog.txt','a')
    words = nltk.word_tokenize(string)

    filter = lambda words: len(words) < 2 or words.isdigit()
    bcf = BigramCollocationFinder.from_words(words)
    bcf.apply_word_filter(filter)

    biResult = bcf.nbest(BigramAssocMeasures.likelihood_ratio, 10)

    tcf = TrigramCollocationFinder.from_words(words)
    tcf.apply_word_filter(filter)

    triResult = tcf.nbest(TrigramAssocMeasures.likelihood_ratio, 4)
    print "\nBigrams:",
    for i in range(len(biResult)):
        biPrint = " ".join(biResult[i])
        print biPrint,"|",
        biList.append(biPrint)
    csvwrite.write('"' + str(biList) + '";')
    print "\nTrigrams:",
    for i in range(len(triResult)):
        triPrint = " ".join(triResult[i])
        print triPrint,"|",
        triList.append(triPrint)
    csvwrite.write('"' + str(triList) + '"\n')

cleanCSV(csvread)
