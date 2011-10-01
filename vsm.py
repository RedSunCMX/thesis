from gensim import corpora,models,similarities
from nltk import WordPunctTokenizer
from nltk.corpus import stopwords
import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
import os
from lxml import etree

corpuslist=[]
cleancorpus=[]

def doCorpus():
    corpustxt = open('corpus.txt','w')
    corpustxt.close()
    directory = "E:\\articles\\articles\\"
    files = os.listdir("E:\\articles\\articles\\")
    for i in range(len(files)):
        currentFile = directory + str(files[i])
        doc = etree.parse(currentFile)
        r = doc.xpath('/art/bdy')
        bdy = r[0]
        results = [ unicode(child.text) for child in bdy.iterdescendants() if child.tag == 'p' and child.text is not None and child.text != '(To access the full article, please see PDF)' and child.text != '"To access the full article, please see PDF"']
        temp = '. '.join(results)
        if len(temp) > 0:
            print files[i]
            clean = ' '.join(cleanDoc(temp))
            corpustxt = open('corpus.txt','a')
            corpustxt.write('"'+clean.encode('utf-8')+'"\n')
            corpustxt.close()
    print len(corpuslist),'articles'

def cleanDoc(doc):
    # Tokenize + remove stopwords of a string
    stopset = set(stopwords.words('english'))    
    tokenString = WordPunctTokenizer().tokenize(doc)
    cleanString = [token.lower() for token in tokenString if token.lower() not in stopset and len(token) > 2]
    return cleanString

def cleanCorpus(corpuslist):
    global cleanCorpus
    for i in range(len(corpuslist)):
        cleancorpus.append(cleanDoc(corpuslist[i]))
    print len(cleancorpus),'articles cleaned'

class MyCorpus(object):
    def __iter__(self):
        for i in range(len(cleancorpus)):
            yield dictionary.doc2bow(cleancorpus[i])

def compareDoc(doc1,doc2):
    doc1 = cleanDoc(doc1)
    doc2 = cleanDoc(doc2)
    bowdoc1 = dictionary.doc2bow(doc1)
    bowdoc2 = dictionary.doc2bow(doc2)
    tfidf1 = tfidf[bowdoc1]
    print len(tfidf1)
    tfidf2 = tfidf[bowdoc2]
    print len(tfidf2)
    index = similarities.MatrixSimilarity([tfidf1],num_features=len(dictionary))
    sims = index[tfidf2]
    print list(enumerate(sims))

doCorpus()
cleanCorpus(corpuslist)
corpus = MyCorpus()
dictionary=corpora.Dictionary(cleancorpus)
print dictionary
tfidf = models.TfidfModel(corpus)
