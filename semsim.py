from SPARQLWrapper import SPARQLWrapper,JSON
import networkx as nx
from networkx.readwrite import json_graph
import sqlite3
import math
from gensim import corpora, models, similarities
from nltk.corpus import stopwords, wordnet
from nltk import word_tokenize, pos_tag, WordPunctTokenizer
import matplotlib.pyplot as plt
import os
from Queue import Queue
import json
GR = nx.Graph()
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

URIx = 'http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#Brain_Lobectomy'
URIy = 'http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#Study'

log = open('pathfinderlog.txt','w')

def main():
    import cyttron
    cyttron.fillDict()
    dicto = cyttron.labelDict   

if __name__ == "__main__":
    main()

def SemSim(URI1,URI2):
    global queue,visited,done,log,path,context
    G = nx.DiGraph()
    q = Queue()
    path=[]
    visited=[]
    # Sort list so node1-node2 == node2-node1
    lijstje=[URI1,URI2]
    start = sorted(lijstje)[0]
    target = sorted(lijstje)[1]

    # Check if URI-path is already in db
    c = conn.cursor()
    c.execute('SELECT * FROM thesis WHERE node1=? AND node2=?',(start,target))

    # If it is, return the data
    if len(c.fetchall()) > 0:
        print "Initial URI Path already exists!",start.rsplit('/')[-1],"-",target.rsplit('/')[-1]
        c.execute('SELECT * FROM thesis WHERE node1=? AND node2=?',(start,target))
        result = c.fetchall()
        c.close()
        start = result[0][0]
        target = result[0][1]
        pathlength = result[0][2]
        path = eval(result[0][3])
        print "SemSim | pathlength:",pathlength
        log = open('pathfinderlog.txt','a')
        log.write('"pathlength";"' + str(pathlength) + '"\n')
        log.close()
        done = True

    # If it's not, start BFS algorithm
    else:
        done = False
        queue = []
        q.put([start])
        
        while not q.empty():
            # Start algorithm, pop value from queue
            curr_path = q.get()
            queue.append(curr_path)
            for i in range(len(curr_path)):
                if len(curr_path) == 1 and len(curr_path[0])>3:
                    # If current path is a single URI, means 1st cycle
                    node = curr_path[0]
                    print "SemSim | Start node:",node
                    visited.append(node)
                    getNodes(node)
                    q.put(context)
                    # context in, path out
                    checkNodes(context,start,target)
                    if len(path) > 0:
                        # print "SemSim |",path
                        path=[]
                        q.empty()
                        return "Done"
                    else:
                        continue
                else:
                    # THIS IS BFS
                    node1 = curr_path[i][0]
                    node2 = curr_path[i][2]
                    #print "\nSemSim | START BFS:\t",dicto[node1],"->",dicto[node2]
                    if node1 not in visited:
                        node = node1
                        visited.append(node)
                        print "GET NEIGHBOURS:\t",node
                        getNodes(node)
                        checkNodes(context,start,target)
                        if len(path) > 0:
                            path=[]
                            q.empty()
                            return "Done"
                        else:
                            q.put(context)
                    elif node2 not in visited:
                        node = node2
                        visited.append(node)
                        print "GET NEIGHBOURS:\t",node
                        getNodes(node)
                        checkNodes(context,start,target)
                        if len(path) > 0:
                            path=[]
                            q.empty()
                            return "Done"
                        else:
                            q.put(context)

def checkNodes(context,URI1,URI2):
    # context in, path out
    global path,queue
    done = False
    
    for i in range(len(context)):
        node1 = context[i][0]
        node2 = context[i][2]
        if node1 == URI2 or node2 == URI2:
            queue.append(context)
            print "\ncheckNodes | FOUND URI2",context[i]
            done = True
            print "checkNodes | URI1:",URI1
            print "checkNodes | URI2:",URI2
            showPath(queue,URI1,URI2)
        else:
            path=[]
            done = False

        if done == True:
            log = open('pathfinderlog.txt','a')                            
            log.write('"pathlength";"' + str(len(path)) + '"\n')
            log.close()
            print "checkNodes | Found a path! Length:",str(len(path)),"| Visited:",str(len(visited)),"nodes."
            c = conn.cursor()
            c.execute('SELECT * FROM thesis WHERE node1=? AND node2=?',(URI1,URI2))
            if len(c.fetchall()) > 0:
                print "checkNodes | Path already exists (wtf?)"
            else:
                print "checkNodes | Inserting path to paths.db."
                c.execute('insert into thesis values (?,?,?,?)',(URI1,URI2,len(path),str(path)))
                conn.commit()
            c.close()
            findFlips(path,URI1,URI2)
            return path
        else:
            continue
    return path

def drawGraph(nodes):   
    global G,path,dicto,pathList,LCS,contextURI
    G = nx.DiGraph()
    
    def drawStart(nodeList):
        color = '#b94431'
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
                            print "START","added",node1
                        else:
                            size = nodeList[j][0]
                            G.add_node(node1)
                            G.node[node1]['color']=color                            
                            G.node[node1]['stroke']=color
                            G.node[node1]['size']=size
                            G.node[node1]['URI']=nodeList[j][2]
                            print "START","added",node1                            
                    if G.has_node(node2) is False:
                        if literal is True:
                            size = nodeList[i][0]                            
                            G.add_node(node2)
                            G.node[node2]['color']=color
                            G.node[node2]['style']='filled'
                            G.node[node2]['size']=size
                            G.node[node2]['URI']=nodeList[i][2]
                            print "START","added",node2                            
                        else:
                            size = nodeList[i][0]
                            G.add_node(node2)
                            G.node[node2]['color']=color                            
                            G.node[node2]['stroke']=color
                            G.node[node2]['size']=size
                            G.node[node2]['URI']=nodeList[i][2]
                            print "START","added",node2                            

    def drawLCS(nodeList):
        color = '#da991c'
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
                        print "\nLCS: added",LCSnode
                        
    def drawBFS(nodeList):
        color = '#333333'
        global path
        path = []
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
                        print "BFS Trying:",otherURI,currentURI
                        SemSim(otherURI,currentURI)
                        print "BFS Finished\n"
                        for i in range(len(path)):
                            node1=str(dicto[path[i][0]])
                            if path[i][1] == 'is a':
                                edge=path[i][1]
                            else:
                                edge=str(dicto[path[i][1]])
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
                            G.edge[node1][node2]['color']='#b94431'
                            G.edge[node1][node2]['width']=2
                            G.edge[node1][node2]['label']=edge
                    else:
                        path = []
                        print "BFS No path possible"

    def drawParents(nodeList):
        color = '#333333'
        global path,dicto,pathList,G,LCS
        G.add_node('Thing')        
        for i in range(len(nodeList)):
            currentURI = nodeList[i][2]
            findParents([[currentURI]])
            CSpec = len(pathList)
            print "PARENTS",nodeList[i][1],"has CSpec:",CSpec
            for i in range(1,len(pathList)):
                for j in range(len(pathList[i])):
                    prevNode = str(dicto[pathList[i][j][0]])
                    node = str(dicto[pathList[i][j][1]])
                    if G.has_node(prevNode) is False:
                        G.add_node(prevNode)
                        if i == CSpec-1:
                            G.node[prevNode]['color'] = 'white'
                        else:
                            G.node[prevNode]['color'] = color
                        G.node[prevNode]['URI'] = pathList[i][j][0]
                        G.node[prevNode]['size']=CSpec
                    if G.has_node(node) is False:
                        G.add_node(node)
                        if i == CSpec-1:
                            G.node[node]['color'] = 'white'
                            G.add_edge(node,'Thing')
                        else:
                            G.node[node]['color'] = color                          
                        G.node[node]['URI']=pathList[i][j][1]
                        G.node[node]['size']=CSpec
                    if G.has_node(node) is True and i == CSpec-1:
                        G.add_edge(node,'Thing')
                        
                    if G.has_edge(prevNode,node) is False:
                        G.add_edge(prevNode,node)
                        G.edge[prevNode][node]['width']=2
                        G.edge[prevNode][node]['label']='subclass of'

    drawStart(nodes)
    print ''
    drawLCS(nodes)
    print ''
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
    print '\nJSON:'
    print s
    print '\nNETWORKX:'
    print G

    #G.graph['layout'] = 'neato'
    #G.add_node('node',fontname='Arial', fontsize='8', fixedsize='true', fontcolor='black', shape='circle', penwidth='5')
    #G.add_node('edge',color='grey', fontcolor='azure4', fontname='Arial', fontsize='7', penwidth='3')

    nx.write_dot(G,'file.gv')
    os.system("gv\\bin\\dot.exe -Tpng -ograph.png file.gv")
    print "Created graph.png"

def clusterSim(nodes):
    G = nx.Graph()
    color = "#b94431"
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
            CSpec = len(pathList)
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
    GR = nx.Graph()
    
    for x in range(len(list),0,-1):
            hop = list[x-1]
            for i in range(len(hop)):
                leftNode = hop[i][0]
                rightNode = hop[i][2]
                GR.add_node(leftNode)
                GR.add_node(rightNode)
                GR.add_edge(leftNode,rightNode)

    print "Drawn Graph: GR"
    spath = (nx.shortest_path(GR,source=start,target=target))
    print spath
    for i in range(1,len(spath)):
        node1 = spath[i-1]
        node2 = spath[i]
        for j in range(len(list)):
            hop = list[j]
            for k in range(len(hop)):
                if node1 in hop[k] and node2 in hop[k] and hop[k] not in path:
                    path.append(hop[k])
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
    # Empties context, returns context
    global context
    context=[]
    c = conn2.cursor()
    c.execute('SELECT * FROM nci WHERE URI=?', (URI,))
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
        querystring="""
        PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?s WHERE { <""" + str(URI) + """> rdfs:subClassOf ?s . FILTER ( isURI(?s )) . }"""
        sparql.setQuery(querystring)        
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            context.append([URI,"is a",x["s"]["value"]])

        # X is_a URI
        querystring="""
        PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?o WHERE { ?o rdfs:subClassOf <""" + str(URI) + """> . FILTER (isURI(?o )) . }"""
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            context.append([x["o"]["value"],'is a',URI])

        # URI part_of X
        querystring="""
        PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl:<http://www.w3.org/2002/07/owl#>

        SELECT DISTINCT ?s ?p WHERE {
        <""" + str(URI) + """> rdfs:subClassOf ?b1 . FILTER ( isBLANK(?b1)) .
        ?b1 owl:someValuesFrom ?s .
        ?b1 owl:onProperty ?p . }"""
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            context.append([URI,x["p"]["value"],x["s"]["value"]])

        # X part_of URI
        querystring="""
        PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl:<http://www.w3.org/2002/07/owl#>
        
        SELECT DISTINCT ?o ?p WHERE {
        ?blank owl:someValuesFrom <""" + str(URI) + """> . FILTER ( isBLANK(?blank)) .
        ?blank owl:onProperty ?p .
        ?o rdfs:subClassOf ?blank . FILTER ( isURI(?o )) . }"""
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            context.append([x["o"]["value"],x["p"]["value"],URI])        

        print len(context),"neighbours (to db)"
        c = conn2.cursor()
        t = (URI,str(context))
        c.execute('insert into nci values (?,?)', t)
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
        print "LCS: " + str(dicto[pathList[0][0]]),"(" + str(dicto[URI1]) + "," + str(dicto[URI2]) + "): "
        log.close()
    else:
        log = open('pathfinderlog.txt','a')                            
        log.write('"LCS depth:-";"0"\n')
        log.close()

def findParents(URI):
    # Returns a pathList which includes all parents per hop in tuples [(child,parent),(child,parent)]
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
    global done,result1,result2,pathList
    result1=[]
    result2=[]
    pathList=[]
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
                    if result1[i][i2][1] == result2[j][j2][1]:
                        done = True
                        if done == True:
                            print "Found COMMON PARENT"
                            return result1[i][i2][1]
    print "No COMMON PARENT"
    return 0
