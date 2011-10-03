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
index = similarities.Similarity.load('vsm\\desc.index')

'''
dictionary = corpora.Dictionary.load('stemcorpus.dict')
print dictionary
corpus = corpora.MmCorpus('stemcorpus.mm')
print corpus
tfidf = models.TfidfModel.load('stemcorpus.tfidf')
print tfidf
'''

# sparql-lists
label = []
desc = []
bigList= []
foundLabel= []
foundDesc= []
URI= []
corpuslist=[]

cyttronKeywords = []
wikiKeywords = []

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
    global label,foundLabel,f,labelDict
    foundLabel=[]
    foundTotal=[]
    foundUnique=[]
    string = string.encode('utf-8')
    f = open('log\wordMatch.csv','a')
    f.write('"' + string + '";"')
    f.close()
    for i in range(len(label)):
        currentLabel = str(label[i][0]).lower()
        currentURI = str(label[i][1])
        string = string.lower()
        c = re.findall(r"\b"+re.escape(currentLabel)+r"\b",string)
        countLabel = len(c)
        if countLabel > 0:
            currentLabel = labelDict[currentURI]
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
        # print foundLabel[i][2],foundLabel[i][0]
        foundURI.append(foundLabel[i][1])
    # print "Found",len(foundUnique),"unique labels"
    # print "and",len(foundTotal),"total labels"
    # print foundURI
    
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
        # print currentWord+str(":"),word
        newString += word
    wordMatch(newString)

# Gensim

def buildCorpus():
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
    print 'Finished'

def cleanDoc(doc):
    stopset = set(stopwords.words('english'))
    stemmer = nltk.PorterStemmer()
    tokens = WordPunctTokenizer().tokenize(doc)
    clean = [token.lower() for token in tokens if token.lower() not in stopset and len(token) > 2]
    # final = [stemmer.stem(word) for word in clean]
    return clean

def compareDoc(doc1,doc2):
    doc1 = cleanDoc(doc1)
    doc2 = cleanDoc(doc2)
    bowdoc1 = dictionary.doc2bow(doc1)
    bowdoc2 = dictionary.doc2bow(doc2)
    tfidf1 = tfidf[bowdoc1]
    tfidf2 = tfidf[bowdoc2]
    index = similarities.MatrixSimilarity([tfidf1],num_features=len(dictionary))
    sim = index[tfidf2]
    print str(round(sim*100,2))+'% similar'

def descMatch(doc):
    global dictionary,desc,labelDict,index
    # disable for cy:
    doc = doc.encode('utf-8')
    fd = open('log\descMatch.csv','a')
    fd.write('"' + doc)
    fd.close()
    #1 clean string, convert to bow, convert to tfidf
    cleanString = cleanDoc(doc)
    bowString = dictionary.doc2bow(cleanString)
    tfidfString = tfidf[bowString]

    #2 clean description, convert to bow, convert to tfidf
    cleanDesc = [cleanDoc(d[0]) for d in desc]
    bowDesc = [dictionary.doc2bow(doc) for doc in cleanDesc]
    tcorpus = tfidf[bowDesc]

    #3 Load index from the descriptions
    sims = index[tfidfString]
#    print "\n"
    for i in range(len(sims)):
        ID = sims[i][0]
        sim = str(sims[i][1]*100)
        sim = sim.encode('utf-8')
        
        descString = desc[ID][0]
        URI = desc[ID][1]
        label = labelDict[URI]

        # label = label.encode('utf-8')
        # descString = descString.encode('utf-8')
        
#        print "Label:",label,"\n","Similarity:",sim,"\n","Description:",descString + "\n"
        fd = open('log\descMatch.csv','a')
        fd.write('";"' + sim + '";"' + label + '";"' + descString)
        fd.close()
    fd = open('log\descMatch.csv','a')    
    fd.write('"\n')
    fd.close()

        
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
    descMatch(newString)
    
#======================================================#
# CyttronDB-specific functions to process lists        #
#======================================================#        
def listWordMatch(list):
    for i in range(len(list)):
        string = list[i]
#        print str(i+1),"of",str(len(list))
        wordMatch(string)
#        print ""

def listWordNetMatch(list):
    for i in range(len(list)):
        string = list[i]
#        print str(i+1),"of",str(len(list))
        wordNetWordMatch(string)
#        print ""

def listDescMatch(lijst):
    for i in range(len(lijst)):
        string = lijst[i]
        descMatch(string)
        print ""

def listWordNetDescMatch(list):
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
        listname.append(line[0])
    print len(listname)

def keywordlist(listname):
    f = csv.reader(open('db\cyttron-keywords.csv', 'rb'), delimiter=';')
    for line in f:
        listname.append(str(line).decode('utf-8'))
    listname.remove(listname[0])
    return listname

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


def stemTxt(sourceList):
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
    stemTxt(cyttronlist)
    print "2/6 Stemming wikilist...",
    stemTxt(wikilist)
    print "3/6 Stemming cyttronKeywords...",
    stemTxt(cyttronKeywords)    
    print "4/6 Stemming wikiKeywords...",
    stemTxt(wikiKeywords)
    print "5/6 Stemming label...",
    stemOnto(label)
    print "6/6 Stemming desc...",
    stemOnto(desc)

def descMatchAll():
    import keywords
    global cyttronKeywords,wikiKeywords,dictionary,corpus,tfidf
    cyttronKeywords = []
    wikiKeywords = []    
    '''
    print "Loading default training corpus..."
    dictionary = corpora.Dictionary.load('vsm\\normal\\corpus.dict')
    print dictionary
    corpus = corpora.MmCorpus('vsm\\normal\\corpus.mm')
    print corpus
    tfidf = models.TfidfModel.load('vsm\\normal\\corpus.tfidf')
    print tfidf    
    '''
    keywords.extractKeywords(cyttronlist,20)
    keywordlist(cyttronKeywords)
    '''
    cProfile.run('listDescMatch(cyttronlist)')
    os.rename('log\descMatch.csv','log\cy-descMatch.csv')
    print "Finished cy-descMatch.csv"

    cProfile.run('listDescMatch(cyttronKeywords)')
    os.rename('log\descMatch.csv','log\cy-descMatch-keyWords.csv')
    print "Finished cy-descMatch-keyWords.csv"

    cProfile.run('listWordNetDescMatch(cyttronKeywords)')
    os.rename('log\descMatch.csv','log\cy-descMatch-keyWords-WordNet.csv')
    print "Finished cy-descMatch-keyWords-WordNet.csv"
    '''
    keywords.extractKeywords(wikilist,20)
    keywordlist(wikiKeywords)
    '''
    cProfile.run('listDescMatch(wikilist)')
    os.rename('log\descMatch.csv','log\wiki-descMatch.csv')
    print "Finished wiki-descMatch.csv"

    cProfile.run('listDescMatch(wikiKeywords)')
    os.rename('log\descMatch.csv','log\wiki-descMatch-keyWords.csv')
    print "Finished wiki-descMatch-keyWords.csv"

    cProfile.run('listWordNetDescMatch(cyttronKeywords)')
    os.rename('log\descMatch.csv','log\wiki-descMatch-keyWords-WordNet.csv')
    print "Finished wiki-descMatch-keyWords-WordNet.csv"    
    '''
    print "\n**********************"
    stemAll()
    print "Loading stemmed training corpus..."
    dictionary = corpora.Dictionary.load('vsm\\stem\\stemcorpus.dict')
    print dictionary
    corpus = corpora.MmCorpus('vsm\\stem\\stemcorpus.mm')
    print corpus
    tfidf = models.TfidfModel.load('vsm\\stem\\stemcorpus.tfidf')
    print tfidf      
    print "**********************\n"
    '''
    cProfile.run('listDescMatch(cyttronlist)')
    os.rename('log\descMatch.csv','log\cy-stem-descMatch.csv')
    print "Finished cy-stem-descMatch.csv"

    cProfile.run('listDescMatch(cyttronKeywords)')
    os.rename('log\descMatch.csv','log\cy-stem-descMatch-keyWords.csv')
    print "Finished cy-stem-descMatch-keyWords.csv"

    cProfile.run('listWordNetDescMatch(cyttronKeywords)')
    os.rename('log\descMatch.csv','log\cy-stem-descMatch-keyWords-WordNet.csv')
    print "Finished cy-stem-descMatch-keyWords-WordNet.csv"
    '''
    cProfile.run('listDescMatch(wikilist)')
    os.rename('log\descMatch.csv','log\wiki-stem-descMatch.csv')
    print "Finished wiki-stem-descMatch.csv"

    cProfile.run('listDescMatch(wikiKeywords)')
    os.rename('log\descMatch.csv','log\wiki-stem-descMatch-keyWords.csv')
    print "Finished wiki-stem-descMatch-keyWords.csv"

    cProfile.run('listWordNetDescMatch(cyttronKeywords)')
    os.rename('log\descMatch.csv','log\wiki-stem-descMatch-keyWords-WordNet.csv')
    print "Finished wiki-stem-descMatch-keyWords-WordNet.csv"   

def wordMatchAll():
    import keywords
    global cyttronKeywords,wikiKeywords
    cyttronKeywords = []
    wikiKeywords = []
    
    # CYTTRON noStem

    keywords.extractKeywords(cyttronlist,20)
    keywordlist(cyttronKeywords)
    
    cProfile.run('listWordMatch(cyttronlist)')
    os.rename('log\wordMatch.csv','log\cy-wordMatch.csv')
    print "Finished cy-wordMatch.csv"

    cProfile.run('listWordMatch(cyttronKeywords)')
    os.rename('log\wordMatch.csv','log\cy-wordMatch-keyWords.csv')
    print "Finished cy-wordMatch-keyWords.csv"

    cProfile.run('listWordNetMatch(cyttronKeywords)')
    os.rename('log\wordMatch.csv','log\cy-wordMatch-keyWords-WordNet.csv')
    print "Finished cy-wordMatch-keyWords-WordNet.csv\nOn to Wiki!"
        
    # WIKI noStem
    
    keywords.extractKeywords(wikilist,20)
    keywordlist(wikiKeywords)
    
    cProfile.run('listWordMatch(wikilist)')
    os.rename('log\wordMatch.csv','log\wiki-wordMatch.csv')
    print "Finished wiki-wordMatch.csv"    
    
    cProfile.run('listWordMatch(wikiKeywords)')
    os.rename('log\wordMatch.csv','log\wiki-wordMatch-keyWords.csv')
    print "Finished wiki-wordMatch-keyWords.csv"

    cProfile.run('listWordNetMatch(wikiKeywords)')
    os.rename('log\wordMatch.csv','log\wiki-wordMatch-keyWords-WordNet.csv')
    print "Finished wiki-wordMatch-keyWords-WordNet.csv"    
    
    print "\n**********************"
    stemAll()
    print "**********************\n"
    
    # CYTTRON stem

    cProfile.run('listWordMatch(cyttronlist)')
    os.rename('log\wordMatch.csv','log\cy-stem-wordMatch.csv')
    print "Finished cy-stem-wordMatch.csv"    

    cProfile.run('listWordMatch(cyttronKeywords)')
    os.rename('log\wordMatch.csv','log\cy-stem-wordMatch-keyWords.csv')
    print "Finished cy-stem-wordMatch-keyWords.csv"

    cProfile.run('listWordNetMatch(cyttronKeywords)')
    os.rename('log\wordMatch.csv','log\cy-stem-wordMatch-keyWords-WordNet.csv')
    print "Finished cy-stem-wordMatch-keyWords-WordNet.csv"
    
    # WIKI stem

    cProfile.run('listWordMatch(wikilist)')
    os.rename('log\wordMatch.csv','log\wiki-stem-wordMatch.csv')
    print "Finished wiki-stem-wordMatch.csv"    
    
    cProfile.run('listWordMatch(wikiKeywords)')
    os.rename('log\wordMatch.csv','log\wiki-stem-wordMatch-keyWords.csv')
    print "Finished wiki-stem-wordMatch-keyWords.csv"

    cProfile.run('listWordNetMatch(wikiKeywords)')
    os.rename('log\wordMatch.csv','log\wiki-stem-wordMatch-keyWords-WordNet.csv')
    print "Finished wiki-stem-wordMatch-keyWords-WordNet.csv"

def main():
    global cyttronlist,wikilist,cyttronKeywords,wikiKeywords
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
