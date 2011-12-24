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
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
import cProfile
import pickle
import cPickle

labelDict = {}
descDict = {}

stopset = set(stopwords.words('english'))
stopset.add('http')
stopset.add('www')

dictionary = corpora.Dictionary.load('newdict.dict')
print dictionary
corpus = corpora.MmCorpus('stemcorpus.mm')
print corpus
tfidf = models.TfidfModel.load('stemtfidf.model')
print tfidf

index = similarities.Similarity.load('stem.index')

labelFile = open('pickle\\label.list','r')
label = pickle.load(labelFile)
labelFile.close()
print "Labels:",len(label)

descFile = open('pickle\\desc.list','r')
desc = pickle.load(descFile)
descFile.close()
print "Descriptions:",len(desc),"\n"

labelDictFile = open('pickle\\labelDict.pickle','r')
labelDict = pickle.load(labelDictFile)
labelDictFile.close()
'''
tfidfFile = open('pickle\\tfidf.pckl','r')
tfidfDesc = pickle.load(tfidfFile)
tfidfFile.close()
print "TF-IDF Descriptions:",len(tfidfDesc),"\n"
'''
# sparql-lists
bigList= []
foundLabel= []
foundDesc=[]
URI= []
corpuslist=[]
simList=[]
cyttronKeywords = []
wikiKeywords = []

cyttronlist = []
csvList = []

wikilist=[]

iup = 0
pathList = []

#teststring
string = "Since AD is associated with a decrease in memory function and the hippocampus might play a role in memory function, researchers focussed on the degeneration of the hippocampus. Bilateral hippocamal atrophy is found in the brains of Alzheimer patients9. Reduction of the hippocampus for diagnosing is measured in two different ways. By using volumetry of the hippocampus itself or by using volumetry of the AHC (amygdale hippocampal complex). Volumetric studies of the hippocampus showed a reduction of 25 -39% 10,11,12. When measuring relative size in relation to the total cranial volume even a bigger reduction is found of 45%10. Yearly measurements of hippocampal volumes in Alzheimer patients showed a 3.98 /-1.92% decrease per year (p < 0.001)6. Patients with severe AD disease show higher atrophy rates compared to early or mild AD10,11. Correlations are found between hippocampal atrophy and severity of dementia, age 11and sex. Because a correlation is found between age and hippocampal atrophy, volumetric changes should be correct for age and sex. For clinical diagnoses it still remains uncertain whether volumetric measurements of the hippocampus alone is the most accurate way, some studies imply so 12. For diagnosing AD by hippocampal volume measurements the sensitivity varies between 77% and 95% and a specificity of 71-92% 9, 11-14. The sensitivity and specificity varies due the variance of patients and controls used. Patients varies in severity of disease and controls in these studies included FTP, MCI or non-alzheimer elderly. Other studies found that diagnosis based on volumetric changes are comparable for the hippocampus and ERC, but due the more easier use and less variability of hippocampal volumetry, the hippocampus is more feasible for diagnosis 13, 15.  Other studies found that combinations of different volumetric measurements with parahippocampal cortex, ERC14or amygdale (see AHC)  are indeed needed for a more accurate diagnosis of AD patients. AD has some similar atrophic regions compared to Mild Cognitive Impairment (MCI), therefore volumetry of the ERC in combination with hippocampal volumetry can give a more accurate diagnosis of AD 14. Total intracranial volume (TIV) and temporal horn indices (THI:  ratio of THV to lateral ventricular volume) can be used as surrogate marker for volume loss of hippocampal formation. A negative correlation is found between THI and THV and the declarative reminding test 16. Some studies indicate that the accuracy of AD diagnosis increases by volumetry of amygdala-hippocampal complex (AHC) compared to only volumetric measurements of the hippocampus 10"
repo="nci"
endpoint="http://localhost:8080/openrdf-sesame/repositories/" + repo

sparql = SPARQLWrapper(endpoint)

wikiTxt=""

f = open('log\wordMatch.csv','w')
f.write('"string";"labels"'+ "\n")
f.close()

fd = open('log\descMatch.csv','w')
fd.write('"string";"over90";"over75";"best5";"best10";"20percent";"10percent"'+ "\n")
fd.close()

csvread = csv.reader(open('db\cyttron-db.csv', 'rb'), delimiter=';')
pub=[]
group=[]
priv=[]

nodes=[]

def get(string):
    global foundLabel,foundDesc,nodes
    foundLabel=[]
    wordMatch(string)
    foundDesc=[]
    descMatch(string)
    nodes = [foundLabel,foundDesc]
    print "found concepts:"
    print len(nodes[0]),"literals"
    print len(nodes[1]),"non-literals"

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
        PREFIX owl: <http://www.w3.org/2002/07/owl#>

        SELECT ?URI ?label
        WHERE {
            ?URI a owl:Class .        
            ?URI rdfs:label ?label .
            }
    """)
    
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        label.append([x["label"]["value"],x["URI"]["value"]])

    print "Filled list: label. With:",str(len(label)),"entries"
    cPickle.dump(label,open('pickle\\label.list','w'))

def fillDict():
    global labelDict,label
    labelDict = {}
    for i in range(len(label)):
        labelDict[label[i][1]] = label[i][0]
    print "Filled dict: labelDict. With:",str(len(labelDict)),"entries"

revDict = {}

def revDict():
    global revDict,label
    for i in range(len(label)):
        labelDict[label[i][0]] = label[i][1]
    print "Filled dict: labelDict. With:",str(len(revDict)),"entries"

descDict = {}

def fillDescDict():
    global descDict,label
    for i in range(len(desc)):
        descDict[desc[i][1]] = desc[i][0]
    print "Filled dict: labelDict. With:",str(len(descDict)),"entries"

def appendDescs():
    global label, descDict
    for i in range(len(label)):
        if label[i][1] in descDict:
            label[i].append(descDict[label[i][1]])

def writeList():
    for i in range(len(label)):
        name = label[i][0]
        uri = label[i][1]
        if len(label[i]) > 2:
            desc = label[i][2]
            listFile.write("<a href=" + uri + ">" + name + "</a> " + "<a title=" + desc + ">*</a>")
        else:
            listFile.write("<a href=" + uri + ">" + name + "</a>")

#======================================================#
# Fill a list of Desc:URI values (Cyttron_DB)          #
#======================================================#
def getDescs():
    global desc,sparql,endpoint
    sparql = SPARQLWrapper(endpoint)
    sparql.addCustomParameter("infer","false")
    sparql.setReturnFormat(JSON)
    # MPATH
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

    print "Round One. filled list: desc. With:",str(len(desc)),"entries"
    # DOID
    sparql.setQuery("""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX newobo:<http://purl.obolibrary.org/obo/>
        
        SELECT ?URI ?desc
        WHERE {
            ?URI a owl:Class .
            ?URI newobo:IAO_0000115 ?desc .
        }
    """)
    
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        desc.append([x["desc"]["value"],x["URI"]["value"]])

    print "Round Two (DOID). filled list: desc. With:",str(len(desc)),"entries"

    # NCI
    sparql.setQuery("""
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX nci:<http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#>

        SELECT ?URI ?def
        WHERE {
            ?URI a owl:Class .
            ?URI nci:DEFINITION ?def .
        }
    """)

    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        ### Strip tags
        p = re.compile(r'<.*?>')
        cleanDesc = p.sub('',x["def"]["value"])
        desc.append((cleanDesc,x["URI"]["value"]))

    print "Round Three. Filled lists: desc. With:",str(len(desc)),"entries"
    cPickle.dump(desc,open('pickle\\desc.list','w'))

#======================================================#
# Scan a string for occurring ontology-words           #
#======================================================#
def wordMatch(string):
    # wordMatch with regexp word boundary
    total = 0
    global label,foundLabel,f,labelDict
    foundLabel=[]
    foundTotal=[]
    foundUnique=[]
    sortFreq=[]
    f = open('log\wordMatch.csv','a')
    f.write('"' + string + '";"')
    f.close()

    for i in range(len(label)):
        labelString = label[i][0].encode('utf-8')
        currentLabel = labelString.lower()
        currentURI = str(label[i][1])
        string = string.lower()
        c = re.findall(r"\b"+re.escape(currentLabel)+r"\b",string)
        countLabel = len(c)
        if countLabel > 0:
            currentLabel = labelDict[currentURI]
            foundLabel.append([countLabel,currentLabel,currentURI])
    foundLabel.sort(reverse=True)
    for i in range(len(foundLabel)):
        total += foundLabel[i][0]
    
    for i in range(len(foundLabel)):
        foundLabel[i][0] = (float(foundLabel[i][0])*0.2)+0.5

    f = open('log\wordMatch.csv','a')
    if len(foundLabel) > 0:
        labels = [found[1] for found in foundLabel]
        f.write(', '.join(labels) + '"\n')
    else:
        f.write('0"\n')
    f.close()

def descMatch(doc):
    global dictionary,desc,labelDict,index,tfidfDesc,foundDesc
    log = open('log\descMatch.csv','a')
    log.write('"' + doc + '";"')
    
    # 1 clean string, convert to bow, convert to tfidf
    cleanString = cleanDoc(doc)
    bowString = dictionary.doc2bow(cleanString)
    tfidfString = tfidf[bowString]

    # 2 Load index of the descriptions
    sims = index[tfidfString]
    sim = []
    for i in range(len(sims)):
        sim.append([round(sims[i],3)+0.5,labelDict[desc[i][1]],desc[i][1]])

    sim = sorted(sim,reverse=True)

    found = []
    for i in range(len(sim)):
        if sim[i][0]-0.5 > 0.4:
            found.append(sim[i])
    #print "over90 (" + str(len(found)) + ")"
    #print found,"\n"
    labels = [str(f[1]) + " (" + str(f[0]) + ")" for f in found]
    log.write(', '.join(labels[:50]))
    log.write('";"')            

    found = []
    for i in range(len(sim)):
        if sim[i][0]-0.5 > 0.25:
            found.append(sim[i])
    #print "over75 (" + str(len(found)) + ")"
    #print found,"\n"
    labels = [str(f[1]) + " (" + str(f[0]) + ")" for f in found]
    log.write(', '.join(labels[:50]))
    log.write('";"')

    found = sim[:5]
    #print "best5 (" + str(len(found)) + ")"
    #print found,"\n"
    labels = [str(f[1]) + " (" + str(f[0]) + ")" for f in found]
    log.write(', '.join(labels[:50]))
    log.write('";"')
    
    found = sim[:10]
    #print "best10 (" + str(len(found)) + ")"
    #print found,"\n"
    labels = [str(f[1]) + " (" + str(f[0]) + ")" for f in found]
    log.write(', '.join(labels[:50]))
    log.write('";"')    

    found = []
    number = sim[0][0]
    for i in range(len(sim)):
        if sim[i][0] > (0.8*number):
            found.append(sim[i])
    #print "percent20 (" + str(len(found)) + ")"
    #print found,"\n"
    labels = [str(f[1]) + " (" + str(f[0]) + ")" for f in found]
    log.write(', '.join(labels[:50]))
    log.write('";"')

    found=[]
    for i in range(len(sim)):
        if sim[i][0] > (0.9*number):
            found.append(sim[i])
    #print "percent10 (" + str(len(found)) + ")"
    #print found,"\n"
    labels = [str(f[1]) + " (" + str(f[0]) + ")" for f in found]
    log.write(', '.join(labels[:50]))
    log.write('"\n')
    log.close()    

#======================================================#
# Scan a string, generate syns for each word           #
# wordMatch syn-string                                 #
#======================================================#
def wordNetWordMatch(string):
    newString = ""
    string = WordPunctTokenizer().tokenize(string)
    for i in range(len(string)):
        currentWord = string[i].lower()
        synonyms = []
        for syn in wordnet.synsets(currentWord):
            for lemma in syn.lemmas:
                synonyms.append(str(lemma.name).replace('_',' ').lower())
        synonyms = set(synonyms)
        word = ', '.join(synonyms)
        newString += word
    wordMatch(newString)

def stemWordNetWordMatch(string):
    newString = ""
    stemmer = nltk.PorterStemmer()    
    string = WordPunctTokenizer().tokenize(string)
    for i in range(len(string)):
        currentWord = string[i].lower()
        synonyms = []
        for syn in wordnet.synsets(currentWord):
            for lemma in syn.lemmas:
                lemma.name = stemmer.stem(lemma.name)
                synonyms.append(str(lemma.name).replace('_',' ').lower())
        synonyms = set(synonyms)
        word = ', '.join(synonyms)
        newString += word
    wordMatch(newString)

#======================================================#
# Gensim stuff                                         #
#                                                      #
#======================================================#

def cleanDoc(doc):
    # String goes in, list of words comes out
    global stopset
    stemmer = nltk.PorterStemmer()
    tokens = WordPunctTokenizer().tokenize(doc)
    clean = [token.lower() for token in tokens if token.lower() not in stopset and len(token) > 1 and token.isalnum() is True]
    final = [stemmer.stem(word) for word in clean]
    return final

def compareDoc(doc1,doc2):
    global sim
    doc1 = cleanDoc(doc1)
    doc2 = cleanDoc(doc2)
    bowdoc1 = dictionary.doc2bow(doc1)
    bowdoc2 = dictionary.doc2bow(doc2)
    tfidf1 = tfidf[bowdoc1]
    tfidf2 = tfidf[bowdoc2]
    index = similarities.MatrixSimilarity([tfidf1],num_features=len(dictionary))
    sim = index[tfidf2]
    sim = round(sim,3)*100
    return sim

def descCompare(string):
    global desc
    flups = []
    for i in range(len(desc)):
        compareDoc(string,desc[i][0])
        flups.append(sim)
    flups = sorted(flups,reverse=True)
    print flups[:10]    

def compare(URI1context,URI2context):
	result1 = compareDoc(str(URI1context[0]),str(URI2context[0]))*1
	result2 = compareDoc(str(URI1context[0]),str(URI2context[1]))*0.5
	result3 = compareDoc(str(URI1context[1]),str(URI2context[0]))*0.5
	result4 = compareDoc(str(URI1context[1]),str(URI2context[1]))*0.25
	print str(result1)+"/100",str(result2)+"/50",str(result3)+"/50",str(result4)+"/25"
	final = (result1+result2+result3+result4)/4
	print str(final)+"% similar"

def vecDesc():
    # Convert desc to TF-IDF
    global desc,tfidfDesc
    tfidfDesc = []
    cleanDesc = [cleanDoc(d[0]) for d in desc]
    bowDesc = [dictionary.doc2bow(doc) for doc in cleanDesc]
    tfidfDesc = [tfidf[d] for d in bowDesc]
    pickle.dump(tfidfDesc,open('pickle\\tfidf.pckl','w'))
    print "converted list desc to vectors (tfidf): vecDesc",len(tfidfDesc)

#======================================================#
# Generate syns from string, gensim similarity         #
#======================================================#    
def descWordNetMatch(string):
    newString = ""
    string = WordPunctTokenizer().tokenize(string)
    for i in range(len(string)):
        currentWord = string[i].lower()
        synonyms = []
        for syn in wordnet.synsets(currentWord):
            for lemma in syn.lemmas:
                synonyms.append(str(lemma.name).replace('_',' ').lower())
        synonyms = set(synonyms)
        word = ', '.join(synonyms)
        newString += word
    print "done"
    descMatch(newString)
    
#======================================================#
# CyttronDB-specific functions to process lists        #
#======================================================#        
def listWordMatch(list):
    for i in range(len(list)):
        string = list[i]
        wordMatch(string)

def listWordNetMatch(list):
    for i in range(len(list)):
        string = list[i]
        wordNetWordMatch(string)

def listStemWordNetMatch(list):
    for i in range(len(list)):
        string = list[i]
        stemWordNetWordMatch(string)

def listDescMatch(lijst):
    fd = open('log\descMatch.csv','w')
    fd.close()    
    for i in range(len(lijst)):
        string = lijst[i]
        descMatch(string)

def listDescWordNetMatch(list):
    fd = open('log\descMatch.csv','w')
    fd.close()      
    for i in range(len(list)):
        string = list[i]
        print str(i+1),"of",str(len(list))
        descWordNetMatch(string)
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
    wikiTxt = wikiTxt.decode('utf-8')
    print title,'in wikiTxt'

# Read cyttron csv and create list
def cyttron(listname):
    f = csv.reader(open('db\cyttron1.csv', 'rb'), delimiter=';')
    for line in f:
        listname.append(line[0])
    print len(listname)

def wordMatchAll(lijst):
    import keywords
    keywords.extractKeywords(lijst,20)
    freqlist = []
    nounlist = []
    bilist = []
    trilist = []
    comboList = []
    
    f = csv.reader(open('db\cyttron-keywords.csv', 'rb'), delimiter=';')
    for line in f:
        freqlist.append(line[0])
        nounlist.append(line[1])
        bilist.append(line[2])
        trilist.append(line[3])
        comboList.append('. '.join(line))

    listWordMatch(lijst)
    os.rename('log\wordMatch.csv','log\wordMatch-literal.csv')
    print "1/24"
    listWordMatch(freqlist)
    os.rename('log\wordMatch.csv','log\wordMatch-freqWords.csv')
    print "2/24"    
    listWordMatch(nounlist)
    os.rename('log\wordMatch.csv','log\wordMatch-nounWords.csv')
    print "3/24"    
    listWordMatch(bilist)
    os.rename('log\wordMatch.csv','log\wordMatch-bigrams.csv')
    print "4/24"    
    listWordMatch(trilist)
    os.rename('log\wordMatch.csv','log\wordMatch-trigrams.csv')
    print "5/24"    
    listWordMatch(comboList)
    os.rename('log\wordMatch.csv','log\wordMatch-combo.csv')
    print "6/24"
    
    listWordNetMatch(lijst)
    os.rename('log\wordMatch.csv','log\wordMatch-wordNet-literal.csv')
    print "7/24"
    listWordNetMatch(freqlist)
    os.rename('log\wordMatch.csv','log\wordMatch-wordNet-freqWords.csv')
    print "8/24"
    listWordNetMatch(nounlist)
    os.rename('log\wordMatch.csv','log\wordMatch-wordNet-nounWords.csv')
    print "9/24"
    listWordNetMatch(bilist)
    os.rename('log\wordMatch.csv','log\wordMatch-wordNet-bigrams.csv')
    print "10/24"
    listWordNetMatch(trilist)
    os.rename('log\wordMatch.csv','log\wordMatch-wordNet-trigrams.csv')
    print "11/24"
    listWordNetMatch(comboList)
    os.rename('log\wordMatch.csv','log\wordMatch-wordNet-combo.csv')
    print "12/24"    

    # Stem
    stemList(lijst)
    stemList(freqlist)
    stemList(nounlist)
    stemList(bilist)
    stemList(trilist)
    stemList(comboList)

    listWordMatch(lijst)
    os.rename('log\wordMatch.csv','log\wordMatch-stem-literal.csv')
    print "13/24"    
    listWordMatch(freqlist)
    os.rename('log\wordMatch.csv','log\wordMatch-stem-freqWords.csv')
    print "14/24"    
    listWordMatch(nounlist)
    os.rename('log\wordMatch.csv','log\wordMatch-stem-nounWords.csv')
    print "15/24"    
    listWordMatch(bilist)
    os.rename('log\wordMatch.csv','log\wordMatch-stem-bigrams.csv')
    print "16/24"
    
    listWordMatch(trilist)
    os.rename('log\wordMatch.csv','log\wordMatch-stem-trigrams.csv')
    print "17/24"    
    listWordMatch(comboList)
    os.rename('log\wordMatch.csv','log\wordMatch-stem-combo.csv')
    print "18/24"    

    listStemWordNetMatch(lijst)
    os.rename('log\wordMatch.csv','log\wordMatch-stem-wordNet-literal.csv')
    print "19/24" 
    listStemWordNetMatch(freqlist)
    os.rename('log\wordMatch.csv','log\wordMatch-stem-wordNet-freqWords.csv')
    print "20/24"

    listStemWordNetMatch(nounlist)
    os.rename('log\wordMatch.csv','log\wordMatch-stem-wordNet-nounWords.csv')
    print "21/24" 
    listStemWordNetMatch(bilist)
    os.rename('log\wordMatch.csv','log\wordMatch-stem-wordNet-bigrams.csv')
    print "22/24" 
    listStemWordNetMatch(trilist)
    os.rename('log\wordMatch.csv','log\wordMatch-stem-wordNet-trigrams.csv')
    print "23/24" 
    listStemWordNetMatch(comboList)
    os.rename('log\wordMatch.csv','log\wordMatch-stem-wordNet-combo.csv')
    print "24/24" 

def stemList(sourceList):
    stemmer = nltk.PorterStemmer()
    templist = []
    for i in range(len(sourceList)):
        templist = []
        tokens = WordPunctTokenizer().tokenize(sourceList[i])
        for j in range(len(tokens)):
            stem = stemmer.stem(tokens[j])
            templist.append(stem)
        sourceList[i] = ' '.join(templist)
    print "Stemmed",len(sourceList),"texts"

# Stem first element of two-element lists
def stemOnto(ontolist):
    stemmer = nltk.PorterStemmer()
    templist = []
    for i in range(len(ontolist)):
        templist=[]
        tokens = WordPunctTokenizer().tokenize(ontolist[i][0])
        for j in range(len(tokens)):
            stem = stemmer.stem(tokens[j])
            templist.append(stem)
        ontolist[i][0] = ' '.join(templist)
    print "Stemmed",len(ontolist),"things"

def stemAll():
    global label,desc,cyttronlist,wikilist,wikiKeywords,cyttronKeywords
    print "1/6 Stemming cyttronlist...",
    stemList(cyttronlist)
    print "2/6 Stemming wikilist...",
    stemList(wikilist)
    print "3/6 Stemming cyttronKeywords...",
    stemList(cyttronKeywords)    
    print "4/6 Stemming wikiKeywords...",
    stemList(wikiKeywords)
    print "5/6 Stemming label...",
    stemOnto(label)
    print "6/6 Stemming desc...",
    stemOnto(desc)

def descMatchAll(lijst):
    import keywords
    keywords.extractKeywords(lijst,20)
    freqlist = []
    nounlist = []
    bilist = []
    trilist = []
    comboList = []
    
    f = csv.reader(open('db\cyttron-keywords.csv', 'rb'), delimiter=';')
    for line in f:
        freqlist.append(line[0])
        nounlist.append(line[1])
        bilist.append(line[2])
        trilist.append(line[3])
        comboList.append('. '.join(line))
    
    listDescMatch(lijst)
    os.rename('log\descMatch.csv','log\descMatch-literal.csv')
    print "1/24"
    listDescMatch(freqlist)
    os.rename('log\descMatch.csv','log\descMatch-freqWords.csv')
    print "2/24"    
    listDescMatch(nounlist)
    os.rename('log\descMatch.csv','log\descMatch-nounWords.csv')
    print "3/24"    
    listDescMatch(bilist)
    os.rename('log\descMatch.csv','log\descMatch-bigrams.csv')
    print "4/24"    
    listDescMatch(trilist)
    os.rename('log\descMatch.csv','log\descMatch-trigrams.csv')
    print "5/24"    
    listDescMatch(comboList)
    os.rename('log\descMatch.csv','log\descMatch-combo.csv')
    print "6/24"
    
    listDescWordNetMatch(lijst)
    os.rename('log\descMatch.csv','log\descMatch-wordNet-literal.csv')
    print "7/24"
    listDescWordNetMatch(freqlist)
    os.rename('log\descMatch.csv','log\descMatch-wordNet-freqWords.csv')
    print "8/24"
    listDescWordNetMatch(nounlist)
    os.rename('log\descMatch.csv','log\descMatch-wordNet-nounWords.csv')
    print "9/24"
    listDescWordNetMatch(bilist)
    os.rename('log\descMatch.csv','log\descMatch-wordNet-bigrams.csv')
    print "10/24"
    listDescWordNetMatch(trilist)
    os.rename('log\descMatch.csv','log\descMatch-wordNet-trigrams.csv')
    print "11/24"
    listDescWordNetMatch(comboList)
    os.rename('log\descMatch.csv','log\descMatch-wordNet-combo.csv')
    print "12/24"

    stemList(lijst)
    stemList(freqlist)
    stemList(nounlist)
    stemList(bilist)
    stemList(trilist)
    stemList(comboList)    

    listDescMatch(lijst)
    os.rename('log\descMatch.csv','log\descMatch-stem-literal.csv')
    print "13/24"
    listDescMatch(freqlist)
    os.rename('log\descMatch.csv','log\descMatch-stem-freqWords.csv')
    print "14/24"    
    listDescMatch(nounlist)
    os.rename('log\descMatch.csv','log\descMatch-stem-nounWords.csv')
    print "15/24"    
    listDescMatch(bilist)
    os.rename('log\descMatch.csv','log\descMatch-stem-bigrams.csv')
    print "16/24"    
    listDescMatch(trilist)
    os.rename('log\descMatch.csv','log\descMatch-stem-trigrams.csv')
    print "17/24"    
    listDescMatch(comboList)
    os.rename('log\descMatch.csv','log\descMatch-stem-combo.csv')
    print "18/24"
    
    listDescWordNetMatch(lijst)
    os.rename('log\descMatch.csv','log\descMatch-stem-wordNet-literal.csv')
    print "19/24"
    listDescWordNetMatch(freqlist)
    os.rename('log\descMatch.csv','log\descMatch-stem-wordNet-freqWords.csv')
    print "20/24"
    listDescWordNetMatch(nounlist)
    os.rename('log\descMatch.csv','log\descMatch-stem-wordNet-nounWords.csv')
    print "21/24"
    listDescWordNetMatch(bilist)
    os.rename('log\descMatch.csv','log\descMatch-stem-wordNet-bigrams.csv')
    print "22/24"
    listDescWordNetMatch(trilist)
    os.rename('log\descMatch.csv','log\descMatch-stem-wordNet-trigrams.csv')
    print "23/24"
    listDescWordNetMatch(comboList)
    os.rename('log\descMatch.csv','log\descMatch-stem-wordNet-combo.csv')
    print "24/24"

def createIndex():
    global desc, dictionary, tfidf, corpus
    cleandesc = [cleanDoc(desc[i][0]) for i in range(len(desc))]
    bowdesc = [dictionary.doc2bow(d) for d in cleandesc]
    vecdesc = tfidf[bowdesc]

def buildCorpus():
    corpustxt = open('corpus.txt','w')
    corpustxt.close()
    directory = "E:\\articles\\articles\\"
    files = os.listdir("E:\\articles\\articles\\")
    for i in range(len(files)):
        doclist = []
        currentFile = directory + str(files[i])
        doc = etree.parse(currentFile)
        r = doc.xpath('/art/bdy')
        bdy = r[0]
        for x in bdy:
            p = x.itertext()
            for j in p:
                if j is not None and 'MathType@' not in j:
                    result = cleanDoc(j)
                    if len(result) > 1:    
                        doclist.append(' '.join(result))
        clean = ' '.join(doclist)
        if len(clean) > 1500:
            print str(i)+":",files[i]
            corpustxt = open('corpus.txt','a')
            corpustxt.write('"' + clean.encode('utf-8') + '"\n')
            corpustxt.close()
    print 'Finished'    

def main():
    global cyttronlist,wikilist,cyttronKeywords,wikiKeywords
    cyttronlist = []
    cyttron(cyttronlist)
    '''
    wikiGet('Alzheimer')
    wikilist.append(wikiTxt)
    wikiGet('Apoptosis')
    wikilist.append(wikiTxt)
    wikiGet('Tau protein')
    wikilist.append(wikiTxt)
    wikiGet('Zebrafish')
    wikilist.append(wikiTxt) 
    print len(wikilist)
    '''
if __name__ == '__main__':
    main()
