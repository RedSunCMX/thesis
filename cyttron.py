# -*- coding: utf-8 -*-

import csv
import nltk
from nltk import word_tokenize, pos_tag, WordPunctTokenizer
from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures
from nltk.corpus import stopwords, wordnet
import re
from SPARQLWrapper import SPARQLWrapper,JSON
from difflib import SequenceMatcher
from pprint import pprint
import urllib, urllib2
from BeautifulSoup import BeautifulSoup
from gensim import corpora, models, similarities
import os
from lxml import etree
import logging 
logging.root.setLevel(logging.INFO)


# sparql-lists
label = []
desc = []
bigList= []
foundLabel= []
foundDesc= []
URI= []
corpuslist=[]

cyttronlist = []
csvList = []

labelDict = {}
wikilist=[]

iup = 0
pathList = []

#teststring
string = "Since AD is associated with a decrease in memory function and the hippocampus might play a role in memory function, researchers focussed on the degeneration of the hippocampus. Bilateral hippocamal atrophy is found in the brains of Alzheimer patients9. Reduction of the hippocampus for diagnosing is measured in two different ways. By using volumetry of the hippocampus itself or by using volumetry of the AHC (amygdale hippocampal complex). Volumetric studies of the hippocampus showed a reduction of 25 -39% 10,11,12. When measuring relative size in relation to the total cranial volume even a bigger reduction is found of 45%10. Yearly measurements of hippocampal volumes in Alzheimer patients showed a 3.98 /-1.92% decrease per year (p < 0.001)6. Patients with severe AD disease show higher atrophy rates compared to early or mild AD10,11. Correlations are found between hippocampal atrophy and severity of dementia, age 11and sex. Because a correlation is found between age and hippocampal atrophy, volumetric changes should be correct for age and sex. For clinical diagnoses it still remains uncertain whether volumetric measurements of the hippocampus alone is the most accurate way, some studies imply so 12. For diagnosing AD by hippocampal volume measurements the sensitivity varies between 77% and 95% and a specificity of 71-92% 9, 11-14. The sensitivity and specificity varies due the variance of patients and controls used. Patients varies in severity of disease and controls in these studies included FTP, MCI or non-alzheimer elderly. Other studies found that diagnosis based on volumetric changes are comparable for the hippocampus and ERC, but due the more easier use and less variability of hippocampal volumetry, the hippocampus is more feasible for diagnosis 13, 15.  Other studies found that combinations of different volumetric measurements with parahippocampal cortex, ERC14or amygdale (see AHC)  are indeed needed for a more accurate diagnosis of AD patients. AD has some similar atrophic regions compared to Mild Cognitive Impairment (MCI), therefore volumetry of the ERC in combination with hippocampal volumetry can give a more accurate diagnosis of AD 14. Total intracranial volume (TIV) and temporal horn indices (THI:  ratio of THV to lateral ventricular volume) can be used as surrogate marker for volume loss of hippocampal formation. A negative correlation is found between THI and THV and the declarative reminding test 16. Some studies indicate that the accuracy of AD diagnosis increases by volumetry of amygdala-hippocampal complex (AHC) compared to only volumetric measurements of the hippocampus 10"
repo="cyttron"
endpoint="http://dvdgrs-900:8080/openrdf-sesame/repositories/" + repo

sparql = SPARQLWrapper(endpoint)

wikiTxt=""

f = open('log\wordMatch.csv','w')
f.write('"string";"# total labels";"total labels";"# unique labels";"unique labels"'+ "\n")
f.close()

fd = open('log\descMatch.csv','w')
fd.close()

csvread = csv.reader(open('db\cyttron-db.csv', 'rb'), delimiter=';')
pub=[]
group=[]
priv=[]

#======================================================#
# Fill a list of Label:URI values (Cyttron_DB)         #
#======================================================#
def getLabels():
    global label,sparql,endpoint
    print endpoint
    sparql = SPARQLWrapper(endpoint)
    sparql.addCustomParameter("infer","false")
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>

        SELECT ?URI ?label
        WHERE {
            ?URI rdfs:label ?label .
            ?URI a owl:Class .
        }
    """)
    
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        label.append([x["label"]["value"],x["URI"]["value"]])

    print "Filled list: label. With:",str(len(label)),"entries"

def wikiLabels():
    global label
    label = []
    endpoint = "http://dvdgrs-900:8080/openrdf-sesame/repositories/dbp"
    print endpoint
    sparql = SPARQLWrapper(endpoint)
    sparql.addCustomParameter("infer","false")
    sparql.setReturnFormat(JSON)
    querystring = 'PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#> select distinct ?label where {?o rdfs:label ?label . filter( langMatches( lang(?label), "en")||(!langMatches(lang(?label),"*")) )}'
    print querystring
    sparql.setQuery(querystring)

    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        label.append([x["label"]["value"],x["URI"]["value"]])   

def fillDict():
    global labelDict,sparql,endpoint
    print endpoint
    sparql = SPARQLWrapper(endpoint)
    sparql.addCustomParameter("infer","false")
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>

        SELECT ?URI ?label
        WHERE {
            ?URI rdfs:label ?label .
            ?URI a owl:Class .
        }
    """)
    
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        labelDict[x["URI"]["value"]] = x["label"]["value"]

    print "Filled dict: labelDict. With:",str(len(labelDict)),"entries"

#======================================================#
# Fill a list of Desc:URI values (Cyttron_DB)          #
#======================================================#
def getDescs():
    global desc,sparql,endpoint
    sparql = SPARQLWrapper(endpoint)
    sparql.addCustomParameter("infer","false")
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>

        SELECT ?URI ?desc
        WHERE {
            ?URI a owl:Class .
            ?URI oboInOwl:hasDefinition ?bnode .
            ?bnode rdfs:label ?desc .
        }
    """)
    
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        desc.append([x["desc"]["value"],x["URI"]["value"]])

    print "filled lists: desc. With:",str(len(desc)),"entries"

#======================================================#
# Scan a string for occurring ontology-words           #
#======================================================#
def wordMatch(string):
    # wordMatch with regexp word boundary
    global label,foundLabel,f
    foundLabel=[]
    foundTotal=[]
    foundUnique=[]
    f = open('log\wordMatch.csv','a')
    f.write('"' + str(string) + '";"')
    f.close()
    for i in range(len(label)):
        currentLabel = str(label[i][0]).lower()
        currentURI = str(label[i][1])
        string = string.lower()
        c = re.findall(r"\b"+re.escape(currentLabel)+r"\b",string)
        countLabel = len(c)
        if countLabel > 0:
            foundLabel.append([countLabel,currentURI,currentLabel])
            foundUnique.append(currentLabel)
            for i in range(countLabel):
                foundTotal.append(currentLabel)
    foundLabel.sort(reverse=True)

    f = open('log\wordMatch.csv','a')
    if len(foundTotal) > 0:
        if len(foundTotal) > 1:
            f.write(str(len(foundTotal)) + '";"' + ', '.join(foundTotal[:-1]) + ', ' + foundTotal[-1] + '";"')
        if len(foundTotal) == 1:
            f.write('1";"' + (foundTotal[0]) + '";"')        
    else:
        f.write('0";"";"')
    if len(foundUnique) > 0:
        if len(foundUnique) > 1:
            f.write(str(len(foundUnique)) + '";"' + ', '.join(foundUnique[:-1]) + ', ' + foundUnique[-1] + '"' + "\n")
        if len(foundUnique) == 1:
            f.write('1";"' + (foundUnique[0]) + '"' + "\n")        
    else:
        f.write('0";""' + "\n")
    f.close()

    foundURI=[]
    for i in range(len(foundLabel)):
        print foundLabel[i][2],foundLabel[i][0]
        foundURI.append(foundLabel[i][1])
    print "Found",len(foundUnique),"unique labels"
    print "and",len(foundTotal),"total labels"
    print foundURI
    
#======================================================#
# Scan a string, generate syns for each word           #
# wordMatch syn-string                                 #
#======================================================#
def wordNetWordMatch(string):
    newString = ""
    string = nltk.word_tokenize(string)
    for i in range(len(string)):
        currentWord = string[i].lower()
        synonyms = []
        for syn in wordnet.synsets(currentWord):
            for lemma in syn.lemmas:
                synonyms.append(str(lemma.name).replace('_',' ').lower())
        synonyms = set(synonyms)
        word = ', '.join(synonyms)
        # print currentWord+str(":"),word
        newString += word
    wordMatch(newString)

#======================================================#
# Use Gensim to calculate similarity                   #
#======================================================#
def descMatch(string,int):
    "Returns the x most similar descriptions"
    temp=[]
    global foundDesc,fd,desc
    fd = open('log\descMatch.csv','a')
    fd.write('"' + string)
    foundDesc=[]
    cleanDesc=[]
    stopset = set(stopwords.words('english'))

    BMCdict=corpora.Dictionary.load('db\\largedict.dict')
    print BMCdict
    mm = corpora.MmCorpus('db\\bmc.mm')
    print mm

    # Initialize model
    tfidf = models.TfidfModel(corpus=mm,dictionary=BMCdict)    
    tokenString = WordPunctTokenizer().tokenize(string)
    cleanString = [token.lower() for token in tokenString if token.lower() not in stopset and len(token) > 2]
    bowString = BMCdict.doc2bow(cleanString)
    print 'bowString:',bowString,'\n'
    tfidfString = tfidf[bowString]
    print 'tfidfString:',tfidfString,'\n'

    ### Compare!
    corpus_tfidf = tfidf[mm]
    print corpus_tfidf
    print "Created corpus_tfidf"
    index = similarities.Similarity('db\\index\\i_',corpus_tfidf,482332,int)
    index.save('db\\bmc.index')
    print "Saved index to db/bmc.index"
    similarity = index[tfidfString]
    print similarity

'''
    sims = sorted(enumerate(sims), key=lambda item: -item[1])
    sims = sims[:int]
    for i in range(len(sims)):
        ID = sims[i][0]
        sim = sims[i][1]
        
        descString = desc[ID][0]
        URI = desc[ID][1]
        label = labelDict[URI]
        
        print "Label:",label,"\n","Similarity:",sim,"\n","Description:",descString + "\n"        
        fd.write('";"' + str(sim) + '";"' + str(label) + '";"' + str(descString))
    fd.write('"\n')
    fd.close()
'''
def trainCorpus():
    # Create a list 'corpuslist' of articles
    global corpuslist
    corpuslist=[]
    directory = "e:\\articles\\articles\\"
    files = os.listdir("e:\\articles\\articles\\")
    for i in range(len(files)):
        currentFile = directory + str(files[i])
        doc = etree.parse(currentFile)
        for x in doc.getiterator('bdy'):
            for y in x[0].getiterator('p'):
                text = y.text
                if text is not None and '(To access the full article, please see PDF)' not in text and len(text)>44:
                    corpuslist.append(text)
    print len(corpuslist)

def createCorpus():
    global corpuslist,desc,BMCdict
    
    stopset = set(stopwords.words('english'))
    cleanList=[]

    # Create a cleanlist (tokenized, stopwords removed) out of all the articles
    for i in range(len(corpuslist)):
        corpusWords = WordPunctTokenizer().tokenize(corpuslist[i])
        cleanWords = [token.lower() for token in corpusWords if token.lower() not in stopset and len(token) > 2]
        cleanList.append(cleanWords)
    print cleanList[324]

    ### Corpus stuff: create a TF-IDF metric using corpuslist
    class MyCorpus(object):
        def __iter__(self):
            for i in range(len(cleanList)):
                yield dictionary.doc2bow(cleanList[i])
    
    # 2. Convert text to vectors, using bag-of-words model
    # Tokenize + clean each corpuslist entry
    dictionary = corpora.Dictionary(cleanList[i] for i in range(len(cleanList)))
    dictionary.compactify()
    dictionary.save('db\\BMC.dict')
    print dictionary

    corpus = MyCorpus()
    print corpus
    tfidf = models.TfidfModel(corpus,id2word=dictionary)
    print tfidf

    corpus_tfidf = tfidf[corpus]
    index = similarities.Similarity(tfidf[corpus_tfidf])
    index.save('db\\bmc.index')
        
#======================================================#
# Generate syns from string, gensim similarity         #
#======================================================#    
def descWordNetMatch(string,int):
    newString = ""
    string = nltk.word_tokenize(string)
    for i in range(len(string)):
        currentWord = string[i].lower()
        synonyms = []
        for syn in wordnet.synsets(currentWord):
            for lemma in syn.lemmas:
                synonyms.append(str(lemma.name).replace('_',' ').lower())
        synonyms = set(synonyms)
        word = ', '.join(synonyms)
        newString += word
    descMatch(newString,int)
    
#======================================================#
# CyttronDB-specific functions to process lists        #
#======================================================#        
def listWordMatch(list):
    for i in range(len(list)):
        string = list[i]
        print str(i+1),"of",str(len(list))
        wordMatch(string)
        print ""

def listWordNetMatch(list):
    for i in range(len(list)):
        string = list[i]
        print str(i+1),"of",str(len(list))
        wordNetWordMatch(string)
        print ""

def listDescMatch(lijst,int):
    for i in range(len(lijst)):
        string = lijst[i]
        print str(i+1),"of",str(len(lijst))
        descMatch(string,int)
        print ""

def listWordNetDescMatch(list,int):
    for i in range(len(list)):
        string = list[i]
        print str(i+1),"of",str(len(list))
        descWordNetMatch(string,int)
        print ""

#======================================================#
# Retrieve Wiki page raw text                          #
#======================================================# 
def wikiGet(title):
    global wikiTxt
    article = urllib.quote(title)

    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')] #wikipedia needs this

    resource = opener.open("http://en.wikipedia.org/wiki/" + article)
    data = resource.read()
    resource.close()
    soup = BeautifulSoup(data)
    text = str(soup.findAll('p'))
    wikiTxt = nltk.clean_html(text)
    wikiTxt = wikiTxt.replace(';','')
    print title,'in wikiTxt'

#======================================================#
# Stuff                                                #
#======================================================# 
def switchEndpoint():
    global endpoint,repo
    if repo == "cyttron":
        repo = "dbp"
        endpoint="http://dvdgrs-900:8080/openrdf-sesame/repositories/" + repo
        print "Switched SPARQL endpoint to DBPedia:",endpoint
        exit
    else:
        repo = "Cyttron_DB"
        endpoint="http://dvdgrs-900:8080/openrdf-sesame/repositories/" + repo
        print "Switched SPARQL endpoint to Cyttron DB:",endpoint
        exit

def cyttron(listname):
    f = csv.reader(open('db\cyttron.csv', 'rb'), delimiter=';')
    for line in f:
        listname.append(str(line[0]))
    print len(listname)

def csv2list(fileName,columnNr):
    global csvList
    csvList=[]
    f = csv.reader(open(fileName,'rb'), delimiter=';')
    for line in f:
        csvList.append(str(line[columnNr]))
    print csvList

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

def main():
    global cyttronlist,wikilist
    cyttronlist = []
    cyttron(cyttronlist)
    getLabels()
    getDescs()
    fillDict()
    wikiGet('Alzheimer')
    wikilist.append(wikiTxt)
    wikiGet('Apoptosis')
    wikilist.append(wikiTxt)
    wikiGet('Tau protein')
    wikilist.append(wikiTxt)
    wikiGet('Zebrafish')
    wikilist.append(wikiTxt) 
    print len(wikilist)

if __name__ == '__main__':
    main()
