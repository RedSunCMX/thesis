from SPARQLWrapper import SPARQLWrapper,JSON
import cyttron
from pygraph.classes.digraph import digraph
from pygraph.readwrite.dot import write
import sqlite3
from gensim import corpora, models, similarities
from nltk.corpus import stopwords, wordnet
from nltk import word_tokenize, pos_tag, WordPunctTokenizer

conn = sqlite3.connect('db/paths.db')
cyttron.fillDict()
dicto = cyttron.labelDict

GR = digraph()
context = []
queue = []
visited = []
path = []
iup = 0
endpoint = 'http://dvdgrs-900:8080/openrdf-sesame/repositories/cyttron'
done = False

URI1 = 'http://purl.org/obo/owl/MPATH#MPATH_127'
URI2 = 'http://purl.org/obo/owl/MPATH#MPATH_154'

s2 = "[u'developmental and adult structural  defect', u'Structural, physical or other general defect of prenatal development of the embryo, the placenta or the adult.', u'MPATH:56', u'Pathbase: Pathology Committee', u'Structural, physical or other general defect of prenatal development of the embryo, the placenta or the adult.', u'developmental and structural abnormality', u'Developmental and structural abnormalities occurring during embryonic development or during adult life.', u'MPATH:55', u'ISBN:0781727286', u'A focal malformation resembling a neoplasm which results from faulty development of an organ; composed of an abnormal mixture of tissue elements, or an abnormal proportion of a single element. Growth and location are usually normal for that tissue cf. Heterotopia/Choristoma MPATH:76/MPATH:477.', u'Pathbase: Curation', u'Any aberration of the normal symmetrical organisation of the body pattern.', u'Pathbase: Pathology Committee', u'Increase in the diameter of an orifice or tubular structure beyond its normal dimensions.', u'ISBN:0781727286', u'Similar to hamartoma, including the mass lesion requirement, but unlike hamartoma, includes heterotopic tissue of an adult or embryonic nature ( topographical and developmental anomaly).', u'Pathbase: Curation', u'Choristoblastoma', u'Pathbase: Pathology Committee', u'The twisting of a bodily organ or part on its own axis.', u'Pathbase: Curation', u'Failure of two cavities, voids or lumens to connect.', u'Pathbase: Curation', u'Aberrant branch or branching pattern of a branched structure such as the bronchus.', u'Pathbase: Curation', u'Inappropriate curvature of a structure.', u'Pathbase: Pathology Committee', u'Formation of an epithelium bounded cavity not associated with neoplasia.', u'Millodot; Michel and Daniel Laby. Dictionary of Ophthalmology. London: Butterworth Heinemann; 2002', u'An adhesion, usually between the iris and the cornea or the lens capsule.', u'ISBN:0781727286', u'Turning in of the edges of a structure.', u'ISBN:0781727286', u'Tearing away or separation of two structures or parts.', u'ISBN:0781727286', u'To sink down, said of an organ or other part. A sinking of an organ or other part, especially its appearance at a natural or artificial orifice.', u'Pathbase: Curation', u'A blind ended outpouching through the wall of a tubular organ or bounded cavity.', u'Pathbase: Curation', u'Additional structure whether normally located or not.', u'Pathbase: Curation', u'An abnormal passage between two internal organs or leading from a cavity to the body surface.', u'Pathbase: Curation', u'Protrusion of a loop or wall of an organ through an abnormal opening.', u'Pathbase: Pathology Committee', u'Occlusion ( partial or complete) of a lumen or space, internally by a space occupying mass or, in the case of stenosis, by local reduction in the diameter of a vessel, duct or the intestine.', u'Pathbase: Pathology Committee', u'Presence of a hole/channel through a normally imperforate structure often a membrane or septum.', u'Pathbase: Curation', u'Embryonic rest.', u'Pathbase: Pathology Committee', u'Persistence of an embryonic structure or tissue into the post-natal period in its normal location; (Chronological/temporal anomaly).', u'Pathbase: Curation', u'Any defect in the formation of septae not describable as perforation.', u'Pathbase: Pathology Committee', u'Localised dilation of an artery or heart chamber usually due to an acquired or congenital weakness of the wall of the artery or chamber.', u'Pathbase: Pathology Committee', u'An enlarged and often tortuous vein.']"
s1="[u'intracellular and extracellular accumulation', u'Accumulation of substances within, on the surface of or between cells.', u'MPATH:33', u'Pathbase: Pathology Committee', u'Accumulation of substances within, on the surface of or between cells.', u'cell and tissue damage', u'The sum of morphological and functional disturbances induced by cell and tissue damage, either from intrinsic gene dysfunction or as a result of external factors.', u'MPATH:1', u'Pathbase: Curation', u'Amyloidosis', u'ISBN:0781727286', u'Extracellular deposition of amyloid protein.', u'ISBN:0781727286', u'Coloration, either normal or pathologic, of the skin or tissues resulting from a deposit of pigment.', u'ISBN:0781727286', u'Deposition of any homogeneous inorganic material.', u'Pathbase: Curation', u'Non-specified intra or extracellular deposition of protein.', u'Pathbase: Curation', u'Intracellular deposition of glycogen.', u'Pathbase: Curation', u'Hyaline degeneration, Eosinophilic cytoplasmic change', u'PMID: 11794381', u'Intracellular deposition of eosinophilic material.', u'Pathbase: Curation', u'Extra or intracellular deposition of lipid.', u'Pathbase: Curation', u'Extracellular deposition of uric acid crystals.', u'Pathbase: Pathology Committee', u'Extracellular accumulation of mucous secretions.', u':Murray AB; Luz A ( 1990 ) Acidophilic macrophage pneumonia in laboratory mice. Vet Pathol.  27; 274-81', u'A mixed inflammatory infiltrate in the pulmonary airways with predominant intra-alveolar macrophage component with intra- and extracellular, elongated, bright eosinophilic/acidophilic crystals.', u'ISBN:0781727286', u'Solid material formed by aggregation of discrete units or particles.', u'Pathbase: Curation', u'fatty change', u'adipose degeneration', u'fatty degeneration', u'Abnormal retention of lipids within a cell. Physically apparent as lipid within liposomes of parenchymal cells.', u'ISBN:9780702027888', u'Swelling of the kidneys when urine flow is obstructed in any of part of the urinary tract.', u'Pathbase: Pathology Committee', u'Accumulation of water in the ventricles of the brain.', u'Pathbase: Curation', u'Intra or extracellular deposition of cholesterol.', u'Pathbase: Curation', u'Accumulation of chitinase-like protein.']"

class MyQUEUE:	
    def __init__(self):
        self.holder = []
    def enqueue(self,val):
        self.holder.append(val)
    def dequeue(self):
        val = None
        try:
            val = self.holder[0]
            if len(self.holder) == 1:
                self.holder = []
            else:
                self.holder = self.holder[1:]	
        except:
            pass	
        return val		
    def IsEmpty(self):
        result = False
        if len(self.holder) == 0:
            result = True
        return result

def SemSim(URI1,URI2):
    q = MyQUEUE()
    BFS(URI1,URI2,q)

def BFS(URI1,URI2,q):
    global queue,visited,done,DG
    # Sort list so node1-node2 == node2-node1
    lijstje=[URI1,URI2]
    URI1 = sorted(lijstje)[0]
    URI2 = sorted(lijstje)[1]

    # Check if initial URI-path is already in db
    c = conn.cursor()
    c.execute('SELECT * FROM thesis WHERE node1=? AND node2=?',(URI1,URI2))
    if len(c.fetchall()) > 0:
        print "Initial URI Path already exists!"
        c.execute('SELECT * FROM thesis WHERE node1=? AND node2=?',(URI1,URI2))
        print c.fetchall()
        c.close()
        done = True
        return 'finished'
    else:
        print "Initial URI Path is unknown to me..."
        done = False
        queue=[]
        visited=[]
        q.enqueue([URI1])
        while q.IsEmpty() == False:
            curr_path = q.dequeue()
            queue.append(curr_path)
            for i in range(len(curr_path)):
                if len(curr_path) > 1:
                    
                    node1 = curr_path[i][0]
                    node2 = curr_path[i][2]
                    edgeLabel = curr_path[i][1]
                    if GR.has_node(node1) is False:
                        GR.add_node(node1)
                    if GR.has_node(node2) is False:
                        GR.add_node(node2)
                    if GR.has_edge((node1,node2)) is False:
                        GR.add_edge((node1,node2),label=str(edgeLabel))

                    # Check if path/edge exists in SQLite DB:
                    c = conn.cursor()
                    c.execute('SELECT * FROM thesis WHERE node1=? AND node2=?',(node1,node2))
                    if len(c.fetchall()) > 0:
                        print "Path already exists!"
                    else:
                        print "Inserting path!"
                        c.execute('insert into thesis values (?,?,1)',(node1,node2))
                        conn.commit()
                    c.close()

                    # print "Added:",node1,">",edgeLabel,">",node2

                    if node1 == URI2:
                        done = True
                        showPath(queue,URI1,URI2)
                        if done == True:
                            string = "Found a link! Stored in path. Length:",len(path),"| Visited:",len(visited),"nodes."
                            print string
                            print path

                            c = conn.cursor()
                            c.execute('SELECT * FROM thesis WHERE node1=? AND node2=?',(URI1,URI2))
                            if len(c.fetchall()) > 0:
                                print "BEST VER Path already exists!"
                            else:
                                print "BEST VER Inserting path!"
                                c.execute('insert into thesis values (?,?,?)',(URI1,URI2,len(path)))
                                conn.commit()
                            c.close()
                            
                            return len(path)
                    if node2 == URI2:
                        print "\nFound a link!"
                        done = True
                        showPath(queue,URI1,URI2)
                        if done == True:
                            string = "Found a link! Stored in path. Length:",len(path),"| Visited:",len(visited),"nodes."
                            print string
                            print path

                            c = conn.cursor()
                            c.execute('SELECT * FROM thesis WHERE node1=? AND node2=?',(URI1,URI2))
                            if len(c.fetchall()) > 0:
                                print "BEST VER Path already exists!"
                            else:
                                print "BEST VER Inserting path!"
                                c.execute('insert into thesis values (?,?,?)',(URI1,URI2,len(path)))
                                conn.commit()
                            c.close()
                    
                            return len(path)
                        
                    if node1 not in visited and 'http://www.w3.org/2002/07/owl#Class' not in node1 and 'http://www.geneontology.org/formats/oboInOwl#ObsoleteClass' not in node1:
                        node = node1
                        visited.append(node)
                        getNodes(node,URI2)
                        q.enqueue(context)
                    else:
                        if 'http://www.w3.org/2002/07/owl#Class' not in node2 and 'http://www.geneontology.org/formats/oboInOwl#ObsoleteClass' not in node2 and node2 not in visited:
                            node = node2
                            visited.append(node)
                            getNodes(node,URI2)
                            q.enqueue(context)
                        else:
                            i+=1
                else:
                    node = curr_path[0]
                    visited.append(node)
                    getNodes(node,URI2)
                    q.enqueue(context)

def createGraph(list_of_nodes):
    global path,dicto,pathList,GR
    for i in range(1,len(list_of_nodes)):
        currentURI = list_of_nodes[i]
        otherURI = list_of_nodes[i-1]
        
        SemSim(otherURI,currentURI)

        # plot BFS result
        for i in range(len(path)):
            nodeLeft = path[i][0]
            edgeLabel = path[i][1]
            nodeRight = path[i][2]
            if GR.has_node(nodeLeft) is False:
                GR.add_node(nodeLeft)
            if GR.has_node(nodeRight) is False:
                GR.add_node(nodeRight)
            if GR.has_edge((nodeLeft,nodeRight)) is False:
                GR.add_edge((nodeLeft,nodeRight),label=str(edgeLabel))

        # plot parent1
        findParents([[URI1]])
        if GR.has_node(pathList[0][0]) is False:
            GR.add_node(pathList[0][0])
        for i in range(1,len(pathList)):
            prevNode = pathList[i-1][0]
            node = pathList[i][0]
            if GR.has_node(node) is False:
                GR.add_node(node)
            if GR.has_edge((prevNode,node)) is False:
                GR.add_edge((prevNode,node),label='rdfs:subClassOf')

        # plot parent2
        findParents([[URI2]])
        if GR.has_node(pathList[0][0]) is False:
            GR.add_node(pathList[0][0])
        for i in range(1,len(pathList)):
            prevNode = pathList[i-1][0]
            node = pathList[i][0]
            if GR.has_node(node) is False:
                GR.add_node(node)
            if GR.has_edge((prevNode,node)) is False:
                GR.add_edge((prevNode,node),label='rdfs:subClassOf')

    # write graph to DOT-file
    dot = write(GR)
    dotLabel = relabel(dot)
    f = open('graph.gv','w')
    f.write(dotLabel)

def relabel(text):
    # from URI to label
    global dicto
    for i, j in dicto.iteritems():
        text = text.replace(i, j)
    return text

def showPath(list,start,target):
    global path
    path = []
    for x in range(len(list),0,-1):
        if x-1 > 1:
            hop = list[x-1]
            for i in range(len(hop)):
                leftNode = hop[i][0]
                rightNode = hop[i][2]
                if leftNode == target:
                    path.append(hop[i])
                    target = rightNode
                    break
                if rightNode == target:
                    path.append(hop[i])
                    target = leftNode
                    break
        if x-1 == 1:
            hop = list[x-1]
            for i in range(len(hop)):
                leftNode = hop[i][0]
                rightNode = hop[i][2]
                if leftNode == start and rightNode == target:
                    path.append(hop[i])
                    findFlips(path,start,target)
                    return path                    
                if rightNode == start and leftNode == target:
                    path.append(hop[i])
                    findFlips(path,start,target)                    
                    return path

def findFlips(path,start,target):
    # START
    left = path[0][0]
    right = path[0][2]
    if left == start:
        # Check to see if path[i+1][0] == right
        # If not: direction flipped
        for i in range(1,len(path)-1):
            if path[i][0] == right:
                print "No flip"
            else:
                print "Direction flipped"

    if right == start:
        for i in range(1,len(path-1)):
            if path[i][2]

def getNodes(URI,URI2):
    global context
    context=[]
    sparql = SPARQLWrapper(endpoint)
    # Direct neighbours
    querystring="SELECT DISTINCT ?p ?s WHERE { <" + str(URI) + "> ?p ?s . FILTER (isURI(?s ))  }"
    print URI
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context.append([URI,x["p"]["value"],x["s"]["value"]])
    querystring="SELECT DISTINCT ?o ?p WHERE { ?o ?p <" + str(URI) + "> . FILTER (isURI(?o )) }"
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context.append([x["o"]["value"],x["p"]["value"],URI])

    # BNode neighbours
    querystring="PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?s2 ?x WHERE { <" + str(URI) + "> ?p ?s . ?s ?x ?s2 . FILTER (isBlank(?s )) . FILTER (isURI(?s2)) .}"
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context.append([URI,x["x"]["value"],x["s2"]["value"]])
    querystring="PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?s2 ?x WHERE { ?o ?p <" + str(URI) + "> . ?s2 ?x ?o . FILTER (isBlank(?o )) . FILTER (isURI(?s2)) .}"
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context.append([x["s2"]["value"],x["x"]["value"],URI])
    return context    

#======================================================#
# 'shared parents' stuff                               #
#======================================================#
def findParents(URI):
    # In: list with list(s) of URIs [[URI1,URI2,URI3]]
    global iup, pathList,endpoint
    list_out=[]
    iup += 1
    print "[findParents]\t","Hop",iup,"found",len(URI[iup-1]),"nodes"
    for i in range(len(URI[iup-1])):
        sparql = SPARQLWrapper(endpoint)
        sparql.addCustomParameter("infer","false")
        querystring = 'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?super WHERE { <' + URI[iup-1][i] + '> rdfs:subClassOf ?super . FILTER isURI(?super) }'
        sparql.setReturnFormat(JSON)
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            list_out.append(x["super"]["value"])
    if len(list_out) > 0:
        URI.append(list_out)
        findParents(URI)
    else:
        print "[findParents]\t","Reached the top!"
        print "[findParents]\t",URI[0][0]
        print "[findParents]\t","Hop | Path:"
        print "[findParents]\t","Depth:",len(URI)
        for i in range(len(URI)):
            print "[findParents]\t",i,"  |",URI[i]
        iup=0
        pathList = URI
        return pathList

def findCommonParents(URI1,URI2):
    global done
    done = False
    # Input URI strings, output common Parent
    print ""
    URI1 = [[URI1]]
    URI2 = [[URI2]]
    iup = 0
    global result1,result2,pathList,parent1,parent2

    # First pathList generation
    findParents(URI1)
    print "[findCommonP]\t","1st URI processed\n"
    result1 = pathList
    
    # Flush results for 2nd
    pathList = []

    # Second pathList generation
    findParents(URI2)
    print "[findCommonP]\t","2nd URI processed\n"
    result2 = pathList

    for i in range(len(result1)):
        for j in range(len(result2)):
            for i2 in range(len(result1[i])):
                for j2 in range(len(result2[j])):
                    if set(result1[i][i2]) == set(result2[j][j2]):
                        print "[findCommonP]\t","CommonParent found!"
                        done = True
                        print "[findCommonP]\t","Result1[" + str(i) + "][" + str(i2) +"]",
                        print "matches with result2[" +str(j) + "][" + str(j2) + "]"
                        print "[findCommonP]\t",result1[i][i2]
                        parent1 = result1
                        parent2 = result2
                        if done == True:
                            return parent1,parent2
    return parent1,parent2

def findMultiParent(URIlist):
    global bigList
    n = len(URIlist)
    for i in range(n):
        for j in range(i+1,n):
            print str(URIlist[i]),"-",str(URIlist[j])
            findCommonParents(URIlist[i],URIlist[j])
            bigList.append([parent1,parent2])


#======================================================#
# Textual comparison                                   #
#======================================================#
def getContext(node1):
    context1=[]
    neighboursOut=[]
    neighboursIn=[]
    sparql = SPARQLWrapper(endpoint)

    # Get own out literals
    querystring="SELECT DISTINCT ?s WHERE { <" + str(node1) + "> ?p ?s . FILTER (isLiteral(?s ))  }"
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        if 'http://www.w3.org/2002/07/owl#Class' not in x["s"]["value"]:
            context1.append(x["s"]["value"])
            print "Own OUT literals:",x["s"]["value"]

    # Get own out bnode-literals
    querystring="PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?desc WHERE { <" + str(node1) + "> ?p ?s . ?s ?x ?desc . FILTER (isBlank(?s )) . FILTER (isLiteral(?desc)) }"
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        if 'http://www.w3.org/2002/07/owl#Class' not in x["s"]["value"]:
            context1.append(x["s"]["value"])
            print "Own OUT bnode-literals:",x["s"]["value"]

    # Get own in literals
    querystring="SELECT DISTINCT ?o WHERE { ?o ?p <" + str(node1) + "> . FILTER (isLiteral(?o )) }"
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context1.append(x["o"]["value"])
        print "Own IN literals",x["o"]["value"]

    # Get own in bnode-literals
    querystring="PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?desc WHERE { ?o ?p <" + str(node1) + "> . ?o ?x ?desc . FILTER (isBlank(?o )) . FILTER (isLiteral(?desc)) }"
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context1.append(x["desc"]["value"])
        print "Own IN literals:",x["desc"]["value"]

    print "Final direct:",context1

    # Get all out neighbour URI's
    querystring="SELECT DISTINCT ?s WHERE { <" + str(node1) + "> ?p ?s . FILTER (isURI(?s ))  }"
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        if 'http://www.w3.org/2002/07/owl#Class' not in x["s"]["value"]:
            neighboursOut.append(x["s"]["value"])
    print "Neighbour OUT nodes:",neighboursOut

    # Get all in neighbour URI's
    querystring="SELECT DISTINCT ?o WHERE { ?o ?p <" + str(node1) + "> . FILTER (isURI(?o )) }"
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        if 'http://www.w3.org/2002/07/owl#Class' not in x["o"]["value"]:
            neighboursIn.append(x["o"]["value"])
    print "Neighbours IN:",neighboursIn

    # Get literal + bnode-literals for OUT neighbours
    for i in range(len(neighboursOut)):
        # Get all neighbour literals
        querystring="SELECT DISTINCT ?s WHERE { <" + str(neighboursOut[i]) + "> ?p ?s . FILTER (isLiteral(?s ))  }"
        sparql.setReturnFormat(JSON)
        sparql.addCustomParameter("infer","false")
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            context1.append(x["s"]["value"])

        # Get all neighbour bnode-literals
        querystring="PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?desc WHERE { <" + str(neighboursOut[i]) + "> ?p ?s . ?s ?x ?desc . FILTER (isBlank(?s )) . FILTER (isLiteral(?desc)) }"
        sparql.setReturnFormat(JSON)
        sparql.addCustomParameter("infer","false")
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            context1.append(x["desc"]["value"])

    # Get literal + bnode-literals for IN neighbours
    for i in range(len(neighboursIn)):
        querystring="SELECT DISTINCT ?o WHERE { ?o ?p <" + str(neighboursIn[i]) + "> . FILTER (isLiteral(?o )) }"
        sparql.setReturnFormat(JSON)
        sparql.addCustomParameter("infer","false")
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            context1.append(x["o"]["value"])

        querystring="PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?desc WHERE { ?o ?p <" + str(neighboursIn[i]) + "> . ?o ?x ?desc . FILTER (isBlank(?o )) . FILTER (isLiteral(?desc)) }"
        sparql.setReturnFormat(JSON)
        sparql.addCustomParameter("infer","false")
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            context1.append(x["desc"]["value"])
    print "Final:",context1

def compareStrings(string1,string2):
    stopset = set(stopwords.words('english'))

    ### Corpus stuff: create a TF-IDF metric using cleaned string1 as training corpus
    # 1. tokenize + clean string1, store in new list
    string1 = [string1]
    words = [[word for word in x.lower().split() if word not in stopset and len(word) > 2] for x in string1]
    print words,"\n"
    
    dictionary = corpora.Dictionary(words)
    print dictionary.token2id,"\n"
    corpus = [dictionary.doc2bow(x) for x in words]

    tfidf = models.TfidfModel(corpus)
    
    ### String stuff: tokenize, clean and convert cleaned String to BOW format using the dictionary generated from the descriptions
    token2 = WordPunctTokenizer().tokenize(string2)
    cleanString = [token.lower() for token in token2 if token.lower() not in stopset and len(token) > 2]
    vec_bow = dictionary.doc2bow(cleanString)
    print "vec_bow:",vec_bow,"\n"
    tfidfString = tfidf[vec_bow]
    
    index = similarities.MatrixSimilarity(tfidf[corpus])
    sims = index[tfidf_string]
    print list(enumerate(sims))
