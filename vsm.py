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
    # Create a list 'corpuslist' of articles
    global corpuslist
    corpuslist=[]
    corpuslist2=[]
    directory = "E:\\articles\\articles\\"
    files = os.listdir("E:\\articles\\articles\\")
    for i in range(1000):
        currentFile = directory + str(files[i])
        print currentFile
        doc = etree.parse(currentFile)
        r = doc.xpath('/art/bdy')
        bdy = r[0]
        results = [ child.text for child in bdy.iterdescendants() if child.tag == 'p' and child.text is not None and child.text != '(To access the full article, please see PDF)' and child.text != '"To access the full article, please see PDF"']
        temp = '. '.join(results)
        if len(temp) > 0:
            corpuslist.append(temp)
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
dictionary=corpora.Dictionary(cleancorpus)
print dictionary
string = 'Since AD is associated with a decrease in memory function and the hippocampus might play a role in memory function, researchers focussed on the degeneration of the hippocampus. Bilateral hippocamal atrophy is found in the brains of Alzheimer patients9. Reduction of the hippocampus for diagnosing is measured in two different ways. By using volumetry of the hippocampus itself or by using volumetry of the AHC (amygdale hippocampal complex). Volumetric studies of the hippocampus showed a reduction of 25 -39% 10,11,12. When measuring relative size in relation to the total cranial volume even a bigger reduction is found of 45%10. Yearly measurements of hippocampal volumes in Alzheimer patients showed a 3.98 /-1.92% decrease per year (p < 0.001)6. Patients with severe AD disease show higher atrophy rates compared to early or mild AD10,11. Correlations are found between hippocampal atrophy and severity of dementia, age 11and sex. Because a correlation is found between age and hippocampal atrophy, volumetric changes should be correct for age and sex. For clinical diagnoses it still remains uncertain whether volumetric measurements of the hippocampus alone is the most accurate way, some studies imply so 12. For diagnosing AD by hippocampal volume measurements the sensitivity varies between 77% and 95% and a specificity of 71-92% 9, 11-14. The sensitivity and specificity varies due the variance of patients and controls used. Patients varies in severity of disease and controls in these studies included FTP, MCI or non-alzheimer elderly. Other studies found that diagnosis based on volumetric changes are comparable for the hippocampus and ERC, but due the more easier use and less variability of hippocampal volumetry, the hippocampus is more feasible for diagnosis 13, 15.  Other studies found that combinations of different volumetric measurements with parahippocampal cortex, ERC14or amygdale (see AHC)  are indeed needed for a more accurate diagnosis of AD patients. AD has some similar atrophic regions compared to Mild Cognitive Impairment (MCI), therefore volumetry of the ERC in combination with hippocampal volumetry can give a more accurate diagnosis of AD 14. Total intracranial volume (TIV) and temporal horn indices (THI:  ratio of THV to lateral ventricular volume) can be used as surrogate marker for volume loss of hippocampal formation. A negative correlation is found between THI and THV and the declarative reminding test 16. Some studies indicate that the accuracy of AD diagnosis increases by volumetry of amygdala-hippocampal complex (AHC) compared to only volumetric measurements of the hippocampus 10'
string_vec = cleanDoc(string)
print string_vec
string_bow = dictionary.doc2bow(string_vec)
print string_bow
corpus = [ dictionary.doc2bow(x) for x in cleancorpus ]
tfidf = models.TfidfModel(corpus)
