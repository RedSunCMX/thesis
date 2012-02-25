from SPARQLWrapper import SPARQLWrapper,JSON
import cyttron
import networkx as nx
from networkx.readwrite import json_graph
import sqlite3
import math
from gensim import corpora, models, similarities
from nltk.corpus import stopwords, wordnet
from nltk import word_tokenize, pos_tag, WordPunctTokenizer
import matplotlib.pyplot as plt
import os
import json

cyttron.fillDict()
dicto = cyttron.labelDict
context = []
queue = []
visited = []
path = []
iup = 0
conn = sqlite3.connect('db/paths.db')
conn2 = sqlite3.connect('db/nodes.db')
endpoint = 'http://localhost:8080/openrdf-sesame/repositories/nci'
LCS = []
#contextURI = 'http://dbpedia.org'
#endpoint = 'http://dbpedia.org/sparql'
#conn = sqlite3.connect('db/dbp.db')
#conn2 = sqlite3.connect('db/dbpnodes.db')
done = False

URIx = 'http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#Frontal_Lobe'
URIy = 'http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#Lobe'

log = open('pathfinderlog.txt','w')

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
    global queue,visited,done,log,path
    q = MyQUEUE()
    
    # Sort list so node1-node2 == node2-node1
    lijstje=[URI1,URI2]
    URI1 = sorted(lijstje)[0]
    URI2 = sorted(lijstje)[1]

    log = open('pathfinderlog.txt','a')                            
    log.write('"node1";"' + str(URI1) + '"\n')
    log.write('"node2";"' + str(URI2) + '"\n')
    log.close()

    # Check if URI-path is already in db
    c = conn.cursor()
    c.execute('SELECT * FROM thesis WHERE node1=? AND node2=?',(URI1,URI2))

    # If it is, return the data
    if len(c.fetchall()) > 0:
        print "Initial URI Path already exists!",URI1.rsplit('/')[-1],"-",URI2.rsplit('/')[-1]
        c.execute('SELECT * FROM thesis WHERE node1=? AND node2=?',(URI1,URI2))
        result = c.fetchall()
        c.close()
        URI1 = result[0][0]
        URI2 = result[0][1]
        pathlength = result[0][2]
        path = eval(result[0][3])
        print "pathlength:",pathlength
        log = open('pathfinderlog.txt','a')
        log.write('"pathlength";"' + str(pathlength) + '"\n')
        log.close()
        done = True

    # If it's not, start BFS algorithm
    else:
        done = False
        queue=[]
        visited=[]
        q.enqueue([URI1])
        while q.IsEmpty() == False:
            curr_path = q.dequeue()
            queue.append(curr_path)
            for i in range(len(curr_path)):
                if len(curr_path) == 1 and len(curr_path[0])>3:
                    # If current path is a single URI, means 1st cycle
                    node = curr_path[0]
                    print "Start node:",node
                    visited.append(node)
                    getNodes(node)
                    q.enqueue(context)

                else:
                    node1 = curr_path[i][0]
                    node2 = curr_path[i][2]
                    edgeLabel = curr_path[i][1]
                    # No target node found: add node to visited list and fetch neighbours (if its not visited + not one of the ignored nodes)
                    if node1 not in visited and 'http://www.w3.org/2002/07/owl#Class' not in node1 and 'http://www.geneontology.org/formats/oboInOwl#ObsoleteClass' not in node1:
                        node = node1
                        visited.append(node)
                        getNodes(node)
                        checkNodes(context,URI1,URI2)
                        if len(path) > 0:
                            print path
                            return "Done"
                        else:
                            # print "No match found..."                            
                            q.enqueue(context)                        
                    elif node2 not in visited and 'http://www.w3.org/2002/07/owl#Class' not in node2 and 'http://www.geneontology.org/formats/oboInOwl#ObsoleteClass' not in node2:
                        node = node2
                        visited.append(node)
                        getNodes(node)
                        checkNodes(context,URI1,URI2)
                        if len(path) > 0:
                            print path
                            return "Done"
                        else:
                            # print "No match found..."
                            q.enqueue(context)

        print 'empty queue. Inserting path=0'
        c.execute('insert into thesis values (?,?,?,?)',(URI1,URI2,0,'[]'))
        conn.commit()
        c.close()

def checkNodes(context,URI1,URI2):
    global path,queue
    done = False
    # print "checking neighbours..."    
    for i in range(len(context)):
        node1 = context[i][0]
        node2 = context[i][2]
        # print "node1:",node1.rsplit('/')[-1],"node2:",node2.rsplit('/')[-1],"\t",URI2.rsplit('/')[-1]
        if node1 == URI2 or node2 == URI2:
            queue.append(context)
            done = True
            print "URI1:",URI1
            print "URI2:",URI2
            showPath(queue,URI1,URI2)
        else:
            done = False
        if done == True:
            string = "Found a link! Stored in path. Length:",len(path),"| Visited:",len(visited),"nodes."
            log = open('pathfinderlog.txt','a')                            
            log.write('"pathlength";"' + str(len(path)) + '"\n')
            log.close()
            print string
            print 'Wrote path to log-file'
            c = conn.cursor()
            c.execute('SELECT * FROM thesis WHERE node1=? AND node2=?',(URI1,URI2))
            if len(c.fetchall()) > 0:
                print "BEST VER Path already exists!"
            else:
                print "BEST VER Inserting path!"
                c.execute('insert into thesis values (?,?,?,?)',(URI1,URI2,len(path),str(path)))
                conn.commit()
            c.close()
            findFlips(path,URI1,URI2)
            return path
    return path

def drawGraph(nodes):
    global path,dicto,pathList,G,LCS,contextURI
    edgelist=[]
    
    # Default settings
    G = nx.DiGraph()

    def drawStart(nodeList):
        color = 'red'
        global path,dicto,pathList,G,LCS        
        # Double for-loop to go through all nodes. Draw start nodes
        for i in range(len(nodeList)):
            currentURI = nodeList[i][2]
            for j in range(i+1,len(nodeList)):
                    node1 = str(dicto[nodeList[j][2]])
                    node2 = str(dicto[nodeList[i][2]])
                    literal = nodeList[j][3]
                    if G.has_node(node1) is False:                    
                        if literal is True:
                            size = nodeList[j][0]
                            G.add_node(node1)
                            G.node[node1]['color']=color
                            G.node[node1]['style']='filled'
                            G.node[node1]['size']=size
                            G.node[node1]['URI']=nodeList[j][2]
                        else:
                            size = nodeList[j][0]
                            G.add_node(node1)
                            G.node[node1]['color']=color                            
                            G.node[node1]['stroke']=color
                            G.node[node1]['size']=size
                            G.node[node1]['URI']=nodeList[j][2]
                    if G.has_node(node2) is False:
                        if literal is True:
                            size = nodeList[i][0]                            
                            G.add_node(node2)
                            G.node[node2]['color']=color
                            G.node[node2]['style']='filled'
                            G.node[node2]['size']=size
                            G.node[node2]['URI']=nodeList[i][2]
                        else:
                            size = nodeList[i][0]
                            G.add_node(node2)
                            G.node[node2]['color']=color                            
                            G.node[node2]['stroke']=color
                            G.node[node2]['size']=size
                            G.node[node2]['URI']=nodeList[i][2]

    def drawLCS(nodeList):
        color = 'orange'
        global path,dicto,pathList,G,LCS        
        # Second double for-loop to go through all the LCSes. Draw LCS.
        for i in range(len(nodeList)):
            currentURI = nodeList[i][2]
            for j in range(i+1,len(nodeList)):
                otherURI = nodeList[j][2]
                findLCS(currentURI,otherURI)
                if LCS[0][0] != 0:
                    LCSnode = str(dicto[LCS[0][0]])
                    if G.has_node(LCSnode) is False:
                        G.add_node(LCSnode)
                        G.node[LCSnode]['color']=color
                        G.node[LCSnode]['URI']=LCS[0][0]

    def drawParents(nodeList):
        color = '#999999'
        global path,dicto,pathList,G,LCS    
        # Third double for-loop to go through all the parents. Draw parents.
        for i in range(len(nodeList)):
            currentURI = nodeList[i][2]
            findParents([[currentURI]])
            for i in range(1,len(pathList)):
                for j in range(len(pathList[i])):
                    print j,
                    print pathList[i][j]
                    prevNode = str(dicto[pathList[i][j][0]])
                    node = str(dicto[pathList[i][j][1]])
                    if G.has_node(prevNode) is False:
                        G.add_node(prevNode)
                        G.node[prevNode]['color'] = color
                        G.node[prevNode]['URI'] = pathList[i][j][0]
                        G.node[prevNode]['size']=0
                    if G.has_node(node) is False:
                        G.add_node(node)
                        G.node[node]['color'] = color
                        G.node[node]['URI']=pathList[i][j][1]
                        G.node[node]['size']=0
                    if G.has_edge(prevNode,node) is False:
                        G.add_edge(prevNode,node)
                        G.edge[prevNode][node]['width']=2
                        
    def drawBFS(nodeList):
        color = '#999999'
        global path
        if len(nodeList) > 0:
            for j in range(len(nodeList)):
                currentURI = nodeList[j][2]
                for k in range(j+1,len(nodeList)):
                    otherURI = nodeList[k][2]
                    findParents([[otherURI]])
                    parentOth = pathList[-1][-1][-1]
                    findParents([[currentURI]])
                    parentCurr = pathList[-1][-1][-1]
                    if parentCurr == parentOth:
                        path=[]
                        print "Trying:",otherURI,currentURI
                        SemSim(otherURI,currentURI)
                        print path
                        print "Finished\n"
                        for i in range(len(path)):
                            node1=str(dicto[path[i][0]])
                            edge=str(path[i][1])
                            node2=str(dicto[path[i][2]])

                            if G.has_node(node1) is False:
                                G.add_node(node1)
                                G.node[node1]['color']=color
                                G.node[node1]['URI']=path[i][0]

                            if G.has_node(node2) is False:                                    
                                G.add_node(node2)
                                G.node[node2]['color']=color
                                G.node[node2]['URI']=path[i][2]

                            G.add_edge(node1,node2)
                            G.edge[node1][node2]['color']='red'
                            G.edge[node1][node2]['width']=2
                    else:
                        print "No path possible\n"

    drawStart(nodes)
    drawLCS(nodes)
    drawBFS(nodes)
    drawParents(nodes)

    # Attributes
    colorlist=[]
    for i in G.node.items():
        if 'color' in i[1]:
            colorlist.append(i[1]['color'])
        else:
            colorlist.append('white')

    sizelist=[]
    for i in G.node.items():
        if 'size' in i[1]:
            sizelist.append(i[1]['size'])
        else:
            sizelist.append(1)

    data = json_graph.node_link_data(G)
    s = json.dumps(data)
    print ''
    print s
    
    #nx.write_dot(G,'file.gv')
    #pos=nx.graphviz_layout(G,prog="neato")
    #nx.draw(G,pos,node_color=colorlist,width=edgelist,arrows=False,node_size=sizelist)
    #plt.show()

def clusterSim(nodes):
    G = nx.Graph()
    color = "red"
    for i in range(len(nodes)):
        current = nodes[i][2]
        currentLabel = dicto[nodes[i][2]]
        size = nodes[i][0]
        G.add_node(currentLabel)
        G.node[currentLabel]['color']=color
        G.node[currentLabel]['size']=size
        G.node[currentLabel]['style']='filled'
        G.node[currentLabel]['URI']=nodes[i][2]
        for j in range(i+1,len(nodes)):
            print current,
            other = nodes[j][2]
            size = nodes[j][0]
            otherLabel = dicto[nodes[j][2]]
            G.add_node(otherLabel)
            G.node[otherLabel]['color']=color
            G.node[otherLabel]['size']=size
            G.node[otherLabel]['style']='filled'
            G.node[otherLabel]['URI']=nodes[j][2]
            print other
            findLCS(current,other)
            CSpec = 15 - len(pathList)
            print "CSpec: ",CSpec

            findParents([[current]])
            parentOth = pathList[-1][-1][-1]
            findParents([[other]])
            parentCurr = pathList[-1][-1][-1]
            if parentCurr == parentOth:
                SemSim(current,other)
                Path = len(path)-1
                semDist = math.log((Path) * (CSpec) + 1)
                print "\nSEMANTIC DISTANCE: ",semDist
                G.add_edge(currentLabel,otherLabel)
                G.edge[currentLabel][otherLabel]['width']=semDist
            else:
                print "No parent"
    data = json_graph.node_link_data(G)
    s = json.dumps(data)
    print s

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
                    return path                    
                if rightNode == start and leftNode == target:
                    path.append(hop[i])
                    return path

def findFlips(path,start,target):
    flips = ""
    count=0
    for i in range(0,len(path)):
        prevLeft = path[i-1][0]
        prevRight = path[i-1][2]
        
        left = path[i][0]
        right = path[i][2]

        if left == prevRight:
            flips += "U"
        if right == prevRight:
            flips += "D"
        if right == prevLeft:
            flips += "D"
    print flips
    for i in range(1,len(flips)):
        prevLetter = flips[i-1]
        letter = flips[i]
        if letter == prevLetter:
            count += 0
        else:
            count += 1
    log = open('pathfinderlog.txt','a')                            
    log.write('"directionflips:";"' + str(count) + '"\n')
    log.close()
    return count

def getNodes(URI):
    global context

    if 'obo/MPATH_' in URI:
        ns = 'mpath'
    if 'obo/DOID_' in URI:
        ns = 'doid'
    if 'EVS/Thesaurus' in URI:
        ns = 'nci'
    if 'http://purl.org/obo/owl/GO' in URI:
        ns='go'
    if 'obo/EHDA_' in URI:
        ns='ehda'
    if '/NCBITaxon' in URI:
        ns='ncbi'

    context=[]
    c = conn2.cursor()
    c.execute('SELECT * FROM ' + str(ns) +' WHERE URI=?', (URI,))
    result = c.fetchall()
    c.close()
    
    if len(result) > 0:
        context = eval(result[0][1])
        c.close()
        return context
    else:
        sparql = SPARQLWrapper(endpoint)
        sparql.setReturnFormat(JSON)
        print URI.rsplit('/')[-1],"has",

        # URI is_a X
        querystring="""PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
SELECT ?s WHERE { <""" + str(URI) + """> rdfs:subClassOf ?s . FILTER ( isURI(?s )) . }"""
        sparql.setQuery(querystring)        
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            if 'http://www.w3.org/' not in x['s']['value']:
                context.append([URI,"is a",x["s"]["value"]])

        if ns == 'go' or ns == 'ehda':
        # URI part_of X
            print "trying part_of rel"
            querystring="""
            PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl:<http://www.w3.org/2002/07/owl#>

            SELECT ?s WHERE {
            <""" + str(URI) + """> rdfs:subClassOf ?b1 . FILTER ( isBLANK(?b1)) .
            ?b1 owl:someValuesFrom ?s . FILTER ( isURI(?s )) . }"""
            sparql.setQuery(querystring)
            results = sparql.query().convert()
            for x in results["results"]["bindings"]:
                if 's' in x:
                    if 'http://www.w3.org/' not in x['s']['value']:            
                        context.append([URI,"is part of",x["s"]["value"]])                

        # X is_a URI
        querystring="""PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?o WHERE {
        { ?o rdfs:subClassOf <""" + str(URI) + """> . FILTER (isURI(?o )) . }
        }"""
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            if 'http://www.w3.org/' not in x['o']['value']:            
                context.append([x["o"]["value"],'is a',URI])

        if ns == 'go' or ns == 'ehda':
        # X part_of URI
            querystring="""
            PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl:<http://www.w3.org/2002/07/owl#>
            SELECT ?o WHERE {
            ?blank owl:someValuesFrom <""" + str(URI) + """> . FILTER ( isBLANK(?blank)) .
            ?o rdfs:subClassOf ?blank . FILTER ( isURI(?o )) . }"""
            sparql.setQuery(querystring)
            results = sparql.query().convert()        
            for x in results["results"]["bindings"]:
                if 's' in x:
                    if 'http://www.w3.org/' not in x['s']['value']:
                        context.append([URI,"is part of",x["s"]["value"]])                  
                
        print len(context),"neighbours (to db)"
        c = conn2.cursor()
        t = (URI,str(context))
        c.execute('insert into ' + str(ns) + ' values (?,?)', t)
        conn2.commit()
        c.close()
    return context
    

#======================================================#
# 'shared parents' stuff                               #
#======================================================#

def findLCS(URI1,URI2):
    global LCS
    LCS = []
    LCS = [[findCommonParents(URI1,URI2)]]
    if LCS[0][0] != 0:
        findParents(LCS)
        log = open('pathfinderlog.txt','a')                            
        log.write('"LCS depth:' + str(pathList[0][0]) + '";"' + str(len(pathList)) + '"\n')
        print "LCS (" + str(dicto[URI1]) + "," + str(dicto[URI2]) + "): ",
        print "LCS: " + str(dicto[pathList[0][0]])
        log.close()
    else:
        log = open('pathfinderlog.txt','a')                            
        log.write('"LCS depth:-";"0"\n')
        print "No LCS"
        log.close()

def findParents(URI):
    # Returns a pathList which includes all parents per hop
    global iup, pathList,endpoint
    list_out=[]
    iup += 1
    if iup == 1:
        sparql = SPARQLWrapper(endpoint)
        sparql.addCustomParameter("infer","false")
        sparql.setReturnFormat(JSON)        
        querystring = 'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?super WHERE { <' + URI[iup-1][0] + '> rdfs:subClassOf ?super . FILTER isURI(?super) }'
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            list_out.append((URI[iup-1][0],x["super"]["value"]))
    else:
        for i in range(len(URI[iup-1])):
            sparql = SPARQLWrapper(endpoint)
            sparql.addCustomParameter("infer","false")
            sparql.setReturnFormat(JSON)
            querystring = 'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?super WHERE { <' + URI[iup-1][i][1] + '> rdfs:subClassOf ?super . FILTER isURI(?super) }'
            sparql.setQuery(querystring)
            results = sparql.query().convert()
            for x in results["results"]["bindings"]:
                list_out.append((URI[iup-1][i][1],x["super"]["value"]))
                
    if len(list_out) > 0:
        URI.append(list_out)
        findParents(URI)
    else:
        iup=0
        pathList = URI
        return pathList

def findCommonParents(URI1,URI2):
    global done,result1,result2,pathList,parent1,parent2
    done = False
    # Input URI strings, output common Parent
    URI1 = [[URI1]]
    URI2 = [[URI2]]
    iup = 0

    # First pathList generation
    findParents(URI1)
    result1 = pathList
    
    # Flush results for 2nd
    pathList = []

    # Second pathList generation
    findParents(URI2)
    result2 = pathList

    for i in range(1,len(result1)):
        for j in range(1,len(result2)):
            for i2 in range(len(result1[i])):
                for j2 in range(len(result2[j])):
                    if set(result1[i][i2][1]) == set(result2[j][j2][1]):
                        done = True
                        parent1 = result1
                        parent2 = result2
                        if done == True:
                            return result1[i][i2][1]
    return 0
