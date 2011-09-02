import csv
import nltk
from nltk import word_tokenize, wordpunct_tokenize, pos_tag
from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures
from nltk.corpus import stopwords
import rdflib
import re
import fuzzywuzzy
from fuzzywuzzy import fuzz
from SPARQLWrapper import SPARQLWrapper

# Read the CSV file to later put into lists
cyttron_csv = csv.reader(open('db\cyttron-db.csv', 'rb'), delimiter=';')
rawCyttron = []

# sparql-lists
label = []
desc = []
uri = []

# other lists
wcollo = []
posdesc = []
a_set = set()
cyttron = []

# Clear file "hack"
csv2 = open('log\csv2.csv','w')
csv2.write('line,column,word occurrence' + '\n')
csv2.close()

cLog = open('log\collocations.txt','w')
cLog.close()

print "sparql()" +'\n' + "> Queries local store (localhost:8080/openrdf-sesame/repositories/Cyttron_DB) for URI's, labels & Descriptions"
print "collo(desc,collo)" + "\n" + "> Creates wordcollocations for each item in list1, outputs to list2"
print "posTag(desc,posdesc)" + "\n" + "> Tokenizes each sentence of list1, Part-Of-Speech tags each word of the tokenized sentences and stores in list2"
print "findTag('NN',posdesc)" + "\n" + "> Find tag 'NN' in list of POS-tagged sentences 'posdesc'"
print "wordMatch(cyttron,label,cyttron_csv,csv2)" + "\n" + "> Match words from label (list of ontology things) from cyttron (lists generated from cyttron_csv). Output to csv2."
print "cleanCSV(cyttron_csv,rawCyttron,a_set,cyttron)" + "\n" + "> Clean CSV, put all entries of list1 into set, all entries of set into list2."

#=======================================================#
# Retrieve descriptions,labels,uri's from OWL-file      #
# Store in 3 separate lists                             #
#=======================================================#

def getLabels():
    sparql = SPARQLWrapper("http://localhost:8080/openrdf-sesame/repositories/Cyttron_DB")
    sparql.addCustomParameter("infer","false")
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
    
    list = []
    results = sparql.query()
    for x in results:
        raw = nltk.clean_html(x)
        if len(raw) > 0:
            list.append(raw)
            
    for i in range(0,len(list),2):
        label.append(list[i])
    for i in range(1,len(list),2):
        uri.append(list[i])

    print "filled lists: uri, label, desc"
    if len(uri) == len(desc) == len(label):
        print "'Things' found: " + str(len(uri))

#=======================================================#
# Create list of collocations (in:list1, out:list2)     #
#=======================================================#
def collo(list,list2):
    stopset = set(stopwords.words('english'))

    for i in range(len(list)):
        words = nltk.word_tokenize(list[i])
        filter = lambda words: len(words) < 3 or words.lower() in stopset
        bcf = BigramCollocationFinder.from_words(words)
        bcf.apply_word_filter(filter)
        result = bcf.nbest(BigramAssocMeasures.likelihood_ratio, 4)
        list2.append(str(result))

    print str(len(list2)) + "x extracted collocations."

#======================================================#
# POS-tag list of OWL-Descs, output new list           #
#======================================================#
def posTag(list,list2):
    for i in range(len(list)):
        line = list[i]
        words = nltk.word_tokenize(line)
        # Maybe: ignore punctuation marks?
        pos  = nltk.pos_tag(words)
        list2.append(pos)
        
        if i == int(0.1*(len(list))):
            print "10% done"
        if i == int(0.2*(len(list))):
            print "20% done"
        if i == int(0.3*(len(list))):
            print "30% done"
        if i == int(0.4*(len(list))):
            print "40% done"
        if i == int(0.5*(len(list))):
            print "50% done"
        if i == int(0.6*(len(list))):
            print "60% done"
        if i == int(0.7*(len(list))):
            print "70% done"
        if i == int(0.8*(len(list))):
            print "80% done"
        if i == int(0.9*(len(list))):
            print "90% done"
    print 'Finished POS-tagging ' + str(len(list2)) + ' sentences'

#======================================================#
# Look up specific types of words (in this case NN)    #
# store in list                                        #
#======================================================#
def findTag(tag_prefix, tagged_text):
    taglog = open('findtags.txt','w')
    n=0
    for i in range(len(tagged_text)):
        n += 1
        cfd = nltk.ConditionalFreqDist((tag, word) for (word, tag) in tagged_text[i] if tag.startswith(tag_prefix) and len(word) > 1)
        nouns = str(dict((tag, cfd[tag].keys()[:5]) for tag in cfd.conditions()))
        taglog.write(str(i+1) + " " + str(nouns) + '\n')
    print 'Filtered ' + str(tag_prefix) + ' from ' + str(n) + ' sentences.'

#======================================================#
# Look up specific types of phrases (in this case NN)  #
# Output:                                              #
#======================================================#
def extractNP(list):
    chunker = RegexpParser(r'''
    NP:
    {<DT><NN.*><.*>*<NN.*>}
    }<VB.*>{
    ''')
    chunker.parse(list[0])

#======================================================#
# Scan a csv for occurring ontology-words              #
#======================================================#
def wordMatch(list,list2,csv,csv2):
    "Scan a csv for occurring ontology-words, output two files: a csv which contains line+column numbers and found words, and a log txt file which contains found word collocations."
    csv2 = open('log\csv2.csv','a')

    pubCount = 0
    groupCount = 0
    privCount = 0
    
    pubTotal = 0
    groupTotal = 0
    privTotal = 0
    
    n = 0
    
    # create a list of lists from the csv
    for line in csv:
        list.append(line)
        n += 1
        
    for i in range(len(list)):
        # Create strings out of each csv cell (split columns)
        pubDesc = str(list[i][0]).lower()
        groupDesc = str(list[i][1]).lower()
        privDesc = str(list[i][2]).lower()

        pubWords = word_tokenize(list[i][0])
	
        for j in range(len(list2)):
            # Match dictionary keys to above created csv cells
            currentLabel = str(list2[j].lower())

            pubCount = pubDesc.count(currentLabel)
            if pubCount > 0:
                print '{0}/1 \t {1}x \t "{2}"'.format(i+1,pubCount,currentLabel)
                csv2.write(str(i+1) + "," + "1" + "," + (currentLabel + ",") * pubCount)
                csv2.write('\n')
                pubTotal += pubCount
                
            groupCount = groupDesc.count(currentLabel)
            if groupCount > 0:
                csv2.write(str(i+1) + "," + "2" + "," + (currentLabel + ",") * groupCount)          
                csv2.write('\n')
                groupTotal += groupCount
            
            privCount = privDesc.count(currentLabel)
            if privCount > 0:
                csv2.write(str(i+1) + "," + "3" + "," + (currentLabel + ",") * privCount)
                csv2.write('\n')
                privTotal += privCount
                
    csv2.close()
    
    print 'Found {0} word occurrences in the public descriptions'.format(pubTotal)
    print 'Found {0} word occurrences in the group descriptions'.format(groupTotal)        
    print 'Found {0} word occurrences in the private descriptions'.format(privTotal)

#======================================================#
# Create a list of word collocations from the csv      #
#======================================================#
def wordCollocations(list,csv):
    "word collocations from"
    stopset = set(stopwords.words('english'))
    cLog = open('log\collocations.txt','a')
    n = 0
    p = re.compile('[0-9]+')
    print "Working..."
    for line in csv:
        list.append(line)
        n += 1

        pubDesc = str(line[0])
        groupDesc = str(line[1])
        privDesc = str(line[2])
        
        pubWords = word_tokenize(pubDesc)
        groupWords = word_tokenize(groupDesc)
        privWords = word_tokenize(privDesc)

        filterPub = lambda pubWords: len(pubWords) < 3 or pubWords.lower() in stopset or p.match(pubWords) is not None
        filterGroup = lambda groupWords: len(groupWords) < 3 or groupWords.lower() in stopset or p.match(groupWords) is not None
        filterPriv = lambda privWords: len(privWords) < 3 or privWords.lower() in stopset or p.match(privWords) is not None

        bcfPub = BigramCollocationFinder.from_words(pubWords)
        bcfGroup = BigramCollocationFinder.from_words(groupWords)
        bcfPriv = BigramCollocationFinder.from_words(privWords)

        bcfPub.apply_word_filter(filterPub)
        bcfGroup.apply_word_filter(filterGroup)
        bcfPriv.apply_word_filter(filterPriv)
        
        resultPub = bcfPub.nbest(BigramAssocMeasures.likelihood_ratio, 4)
        resultGroup = bcfGroup.nbest(BigramAssocMeasures.likelihood_ratio, 4)
        resultPriv = bcfPriv.nbest(BigramAssocMeasures.likelihood_ratio, 4)
        
        if len(resultPub) > 0:
            cLog.write(str(n) + '/1 ' + str(resultPub) + '\n')
        if len(resultGroup) > 0:        
            cLog.write(str(n) + '/2 ' + str(resultGroup) + '\n')
        if len(resultPriv) > 0:
            cLog.write(str(n) + '/3 ' + str(resultPriv) + '\n')
    print "Done."
    cLog.close()

#=======================================================#
# Clean up CSV                             	        #
# Remove duplicates + empty entries                     #
# ** W I P **                                           #
#=======================================================#
def cleanCSV(csv,list,a_set,tupleCsv):
    "Clean up csv by removing duplicate content, removing newline characters"
    counter = 0
    for line in csv:
        list.append(line)
    print len(list)

    tupleCsv = tuple(list)
    a_set = sorted(tupleCSV)        
    
### TODO:
# If > 1 ontology word occurrence, SPARQL query(?) to discover how terms relate to one another?
# If 0 word occurrences, match OWL descriptions with csv entry.
# Create keyword list from ontology descriptions
# Fix encoding / special characters
