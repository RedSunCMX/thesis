import csv
import nltk
from nltk import word_tokenize, pos_tag, WordPunctTokenizer
from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures
from nltk.corpus import stopwords, wordnet
import re
from SPARQLWrapper import SPARQLWrapper,JSON
from pprint import pprint
from gensim import corpora, models, similarities
import os
from lxml import etree
import cPickle
import pickle
from xml.dom.minidom import parse
import semsim

stopset = set(stopwords.words('english'))
stopset.add('http')
stopset.add('www')
stopset.add('nci')

# --- GenSim Stuff
dictionary = corpora.Dictionary.load('vsm\\normal\\normal-dictionary.dict')
print dictionary
corpus = corpora.MmCorpus('vsm\\normal\\normal-corpus.mm')
print corpus
tfidf = models.TfidfModel.load('vsm\\normal\\normal-tfidf.model')
print tfidf

index = similarities.Similarity.load('vsm\\normal\\normal-index.index')

tfidfFile = open('vsm\\normal\\tfidfDesc.list','r')
tfidfDesc = pickle.load(tfidfFile)
tfidfFile.close()
print "TF-IDF Descriptions:",len(tfidfDesc),"\n"
'''
dictionary = corpora.Dictionary.load('vsm\\stem\\stem-dictionary.dict')
print dictionary
corpus = corpora.MmCorpus('vsm\\stem\\stem-corpus.mm')
print corpus
tfidf = models.TfidfModel.load('vsm\\stem\\stem-tfidf.model')
print tfidf

index = similarities.Similarity.load('vsm\\stem\\stem-index.index')

tfidfFile = open('vsm\\stem\\tfidfDesc.list','r')
tfidfDesc = pickle.load(tfidfFile)
tfidfFile.close()
print "TF-IDF Descriptions:",len(tfidfDesc),"\n"
# ---
'''
labelFile = open('pickle\\label.list','r')
label = pickle.load(labelFile)
labelFile.close()
print "Labels:",len(label)

descFile = open('pickle\\desc.list','r')
desc = pickle.load(descFile)
descFile.close()
print "Descriptions:",len(desc),"\n"

labelDict={}
labelDictFile = open('pickle\\labelDict.list','r')
labelDict = pickle.load(labelDictFile)
labelDictFile.close()

revDictFile = open('pickle\\revDict.list','r')
revDict = pickle.load(revDictFile)
revDictFile.close()

descDictFile = open('pickle\\descDict.list','r')
descDict = pickle.load(descDictFile)
descDictFile.close()

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
cyttronAll = []
csvList = []

wikilist=[]

iup = 0
pathList = []

#teststring
repo="nci"
endpoint="http://localhost:8080/openrdf-sesame/repositories/" + repo

sparql = SPARQLWrapper(endpoint)

f = open('log\wordMatch.csv','w')
f.close()

fd = open('log\descMatch.csv','w')
fd.close()

pub=[]
group=[]
priv=[]
props = []
nodes=[]

def get(string):
    global foundLabel,foundDesc,nodes
    foundLabel=[]
    wordMatch(string)
    # append item
    for i in range(len(foundLabel)):
        foundLabel[i].append(True)
    foundDesc=[]
    descMatch(string)
    for i in range(len(foundDesc)):
        foundDesc[i].append(False)
    nodes = foundLabel + foundDesc
    print "found concepts:"
    print len(nodes[0]),"literals"
    print len(nodes[1]),"non-literals"

#======================================================#
# Fill a list of Label:URI values (Cyttron_DB)         #
#======================================================#
def getLabels():
    global label,sparql,endpoint
    label = []
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
    print "LABEL | Filled list: label. With:",str(len(label)),"entries"

    # Fetch 'Part_Of' properties
    sparql.setQuery("""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>

        SELECT ?URI ?label
        WHERE {
            ?URI a owl:ObjectProperty .        
            ?URI rdfs:label ?label .
            }""")
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        if 'part_of' in x["label"]["value"].lower():
            label.append([x["label"]["value"],x["URI"]["value"]])
    print "LABEL | Filled list: label. With:",str(len(label)),"entries"

    cPickle.dump(label,open('pickle\\label.list','w'))

def fillDict():
    global labelDict,label
    labelDict = {}
    for i in range(len(label)):
        labelDict[label[i][1]] = label[i][0]
    print "Filled dict: labelDict. With:",str(len(labelDict)),"entries"

    cPickle.dump(label,open('pickle\\labelDict.list','w'))

def fillDescDict():
    global descDict,label
    descDict = {}
    for i in range(len(desc)):
        descDict[desc[i][1]] = desc[i][0]
    print "Filled dict: descDict. With:",str(len(descDict)),"entries"
    cPickle.dump(descDict,open('pickle\\descDict.list','w'))    

def fillRevDict():
    global revDict,label
    revDict = {}
    for i in range(len(label)):
        revDict[label[i][0]] = label[i][1]
    print "Filled dict: revDict. With:",str(len(revDict)),"entries"
    cPickle.dump(revDict,open('pickle\\revDict.list','w'))    

def URItoNodes(URIs,number):
    newList=[]
    list = URIs.split(',')
    for i in range(len(list)):
        if labelDict[list[i]].lower() in cyttronlist[number].lower():
            newList.append([list[i],True])
        else:
            newList.append([list[i],False])
    print newList

def csvToNodes():
    directory = "log\\expert\\"
    files = os.listdir(directory)
    for i in range(len(files)):
        newList=[]
        csvtje = csv.reader(open(str(directory) + str(files[i]),'rb'),delimiter=';',quotechar='"')
        print files[i]
        for line in csvtje:
                temp = line[1].split(',')
                for j in range(1,len(temp)):
                    uri = str(temp[j]).replace(' ','')
                    currLabel = labelDict[uri]
                    if currLabel.lower() in line[0].lower():
                        newList.append([uri,True])
                    else:
                        newList.append([uri,False])
        print newList

def buildMatrix():
    '''
    Confusion Matrix
    http://www2.cs.uregina.ca/~hamilton/courses/831/notes/confusion_matrix/confusion_matrix.html
    '''

    matrix = []
    prList = []
    f = open('log\\confmatrix.csv','w')
    f.write('"Algorithm";"Accuracy";"True Positives";"False Positives";"True Negatives";"False Negatives";"Precision"\n')
    f.close()
    algoDir = "log\\DEF\\"
    expertDir = "log\\expert\\"
    URIlist = [l[1] for l in label]
    # Fill list with expert results
    files = os.listdir(expertDir)
    for i in range(len(files)):
        expertList = []
        csvtje = csv.reader(open(str(expertDir) + str(files[i]),'rb'),delimiter=';',quotechar='"')
        for line in csvtje:
            tempList=[]
            temp = line[1].split(',')
            for j in range(1,len(temp)):
                uri = str(temp[j]).replace(' ','')
                tempList.append(uri)
            print len(tempList),"URIs"                
            expertList.append(tempList)
    print "expertList:",expertList

    # Fill list with algo results
    files = os.listdir(algoDir)
    for i in range(len(files)):
        algoList = []
        print files[i]
        
        # print "\n",files[i]
        csvtje = csv.reader(open(str(algoDir) + str(files[i]),'rb'),delimiter=';',quotechar='"')
        for line in csvtje:
            tempList=[]
            temp = line[1].split(',')
            for j in range(len(temp)):
                uri = str(temp[j]).replace(' ','')
                tempList.append(uri)
            algoList.append(tempList)

        if len(algoList) == 9:
            algoList = algoList[1:]

        A = 0.0
        B = 0.0
        C = 0.0
        D = 0.0
        
        for j in range(len(algoList)):
            algoPOS = algoList[j]
            algoNEG = [item for item in URIlist if item not in algoList[j]]
            expertPOS = expertList[j]
            expertNEG = [item for item in URIlist if item not in expertList[j]]
            
            A += float(len(set(algoNEG).intersection(expertNEG)))
            B += float(len(set(algoPOS).intersection(expertNEG)))
            C += float(len(set(algoNEG).intersection(expertPOS)))
            D += float(len(set(algoPOS).intersection(expertPOS)))

        matrix.append([[A,B],[C,D]])
        
        AC = ((A+D) / (A+B+C+D))
        TP = ((D) / (C+D))
        FP = ((B) / (A+B))
        TN = ((A) / (A+B))
        FN = ((C) / (C+D))
        if (B+D) > 0:
            P = ((D) / (B+D))
        else:
            P = 0
        
        print "AC",round(AC,4),
        print "TP",round(TP,4),
        print "FP",round(FP,4),
        print "TN",round(TN,4),
        print "FN",round(FN,4),
        print "P",round(P,4)
        
        prList.append([files[i],AC,TP,FP,TN,FN,P])
    pprint(prList)
    pprint(matrix)
    for i in range(len(prList)):
        f = open('log\\confmatrix.csv','a')
        f.write('"' + str(prList[i][0]) + '";"' + str(prList[i][1]) + '";"' + str(prList[i][2]) + '";"' + str(prList[i][3]) + '";"' + str(prList[i][4]) + '";"' + str(prList[i][5]) + '";"' + str(prList[i][6]) + '"\n')
        f.close()
        
#======================================================#
# Fill a list of Desc:URI values (Cyttron_DB)          #
#======================================================#
def getDescs():
    global desc,sparql,endpoint
    sparql = SPARQLWrapper(endpoint)
    sparql.addCustomParameter("infer","false")
    sparql.setReturnFormat(JSON)
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

    sparql.setQuery("""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX nci:<http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#>

        SELECT ?URI ?def
        WHERE {
            ?URI a owl:ObjectProperty .        
            ?URI nci:DEFINITION ?def .
            }""")
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        if 'part_of' in x["def"]["value"].lower():
            desc.append([x["def"]["value"],x["URI"]["value"]])        

    print "Filled lists: desc. With:",str(len(desc)),"entries"
    cPickle.dump(desc,open('pickle\\desc.list','w'))

#======================================================#
# Scan a string for occurring ontology-words           #
#======================================================#
def wordMatch(string):
    # wordMatch with regexp word boundary
    total = 0
    global label,foundLabel,f,labelDict
    foundLabel=[]
    f = open('log\wordMatch.csv','a')
    f.write('"' + string + '";"')
    f.close()

    for i in range(len(label)):
        currentLabel = label[i][0].encode('utf-8').lower()
        currentURI = str(label[i][1])
        string = string.lower()
        c = re.findall(r"\b"+re.escape(currentLabel)+r"\b",string)
        if len(c)>0:
            foundLabel.append(currentURI)

    f = open('log\wordMatch.csv','a')
    if len(foundLabel) > 0:
        print "Found",len(foundLabel),"words"
        f.write(','.join(foundLabel) + '"\n')
    else:
        f.write('0"\n')
        print "Found 0 words"
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
        sim.append([round(sims[i],3)+0.5,desc[i][1]])
    sim = sorted(sim,reverse=True)

    # Over 90%
    found = []
    for i in range(len(sim)):
        if sim[i][0]-0.5 > 0.4:
            found.append(sim[i][1])
    print "over90 (" + str(len(found)) + ")"
    log.write(','.join(found))
    log.write('";"')            

    # Over 75%
    found = []
    for i in range(len(sim)):
        if sim[i][0]-0.5 > 0.25:
            found.append(sim[i][1])
    print "over75 (" + str(len(found)) + ")"
    log.write(','.join(found))
    log.write('";"')    

    # Top5
    found = sim[:5]
    print "best5 (" + str(len(found)) + ")"
    uris = [str(f[1]) for f in found]
    log.write(','.join(uris))
    log.write('";"')    

    found = sim[:10]
    print "best10 (" + str(len(found)) + ")"
    uris = [str(f[1]) for f in found]
    log.write(','.join(uris))
    log.write('";"')    

    found = []
    number = sim[0][0]
    for i in range(len(sim)):
        if sim[i][0] > (0.8*number):
            found.append(sim[i][1])
    print "percent20 (" + str(len(found)) + ")"
    log.write(','.join(found))
    log.write('";"')    

    found=[]
    for i in range(len(sim)):
        if sim[i][0] > (0.9*number):
            found.append(sim[i])
    print "percent10 (" + str(len(found)) + ")"

    foundDesc = found
    log.write(','.join(found))
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
    pickle.dump(tfidfDesc,open('vsm\\stem\\tfidf.pckl','w'))
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
    print "\n"
    for i in range(len(list)):
        print i+1,
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

# Read cyttron csv and create list
def cyttron(listname):
    f = csv.reader(open('db\cyttron-selection.csv', 'rb'), delimiter=';')
    for line in f:
        listname.append(line[0])
    print len(listname)

def cyttronCorpus(listname):
    f = csv.reader(open('db\cyttron-clean.csv', 'rb'), delimiter=';')
    for line in f:
        listname.append(line[0])
    print len(listname)

def wordMatchAll(lijst):
    import keywords
    global cyttronAll
    keywords.extractKeywords(lijst,cyttronAll,20)
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
    print comboList[1]
    
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
    stemOnto(label)
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
        print sourceList[i]
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

    dictionary = corpora.Dictionary.load('vsm\\stem\\stem-dictionary.dict')
    print dictionary
    corpus = corpora.MmCorpus('vsm\\stem\\stem-corpus.mm')
    print corpus
    tfidf = models.TfidfModel.load('vsm\\stem\\model.tfidf')
    print tfidf

    index = similarities.Similarity.load('vsm\\stem\\stem.index')

    tfidfFile = open('vsm\\stem\\tfidfDesc.list','r')
    tfidfDesc = pickle.load(tfidfFile)
    tfidfFile.close()
    print "TF-IDF Descriptions:",len(tfidfDesc),"\n"    

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
    directory = "E:\\articles\\articles\\"
    files = os.listdir(directory)
    blank = "To access the full article, please see PDF"
    for i in range(len(files)):
        doclist = []
        currentFile = directory + str(files[i])
        doc = etree.parse(currentFile)
        r = doc.xpath('/art/bdy')
        bdy = r[0]
        for x in bdy:
            p = x.itertext()
            for j in p: 
                if 'MathType@' not in j and blank not in j and not j.isspace() and len(j)>15:
                    result = cleanDoc(j)
                    if len(result) > 3:
                        doclist.append(' '.join(result))
        if len(doclist) > 0:
            clean = ' '.join(doclist)
            print str(i)+":",files[i]
            corpustxt = open('vsm\\stem\\stem-corpus.txt','a')
            corpustxt.write('"' + clean.encode('utf-8') + '"\n')
            corpustxt.close()
    print 'Finished'

def main():
    global cyttronlist,cyttronAll,cyttronKeywords
    cyttronlist = []
    cyttron(cyttronlist)
    cyttronCorpus(cyttronAll)
    
if __name__ == '__main__':
    main()
