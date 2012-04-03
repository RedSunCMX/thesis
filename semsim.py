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
import csv

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
done = False
dicto = {}

def main():
    global dicto
    import cyttron
    cyttron.fillDict()
    dicto = cyttron.labelDict   

if __name__ == "__main__":
    main()

def pathFinder(URI1,URI2):
    global queue,visited,done,log,path,pathlength,context
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
        c.execute('SELECT * FROM thesis WHERE node1=? AND node2=?',(start,target))
        result = c.fetchall()
        c.close()
        start = result[0][0]
        target = result[0][1]
        pathlength = result[0][2]
        path = eval(result[0][3])
        # print "pathFinder | pathlength:",pathlength
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
                    print "pathFinder | Start node:",node
                    visited.append(node)
                    getNodes(node)
                    q.put(context)
                    # context in, path out
                    checkNodes(context,start,target)
                    if len(path) > 0:
                        path=[]
                        q.empty()
                        return "Done"
                    else:
                        continue
                else:
                    # THIS IS BFS
                    node1 = curr_path[i][0]
                    node2 = curr_path[i][2]
                    if node1 not in visited:
                        node = node1
                        visited.append(node)
                        # print "GET NEIGHBOURS:\t",node
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
                        # print "GET NEIGHBOURS:\t",node
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
            return path
        else:
            continue
    return path

def drawGraph(URIlist):   
    global G,path,dicto,pathList,LCS,contextURI
    G = nx.DiGraph()
    G.add_node('Thing')        
    iup = 0
    
    def drawStart(nodeList):
        global path,dicto,pathList,G,LCS        
        # Double for-loop to go through all nodes. Draw start nodes
        for i in range(len(nodeList)):
            for j in range(i+1,len(nodeList)):
                    uri1 = nodeList[j]
                    node1 = dicto[nodeList[j]]
                    findParents([[uri1]])
                    depth1 = len(pathList)

                    uri2 = nodeList[i]
                    node2 = dicto[nodeList[i]]
                    findParents([[uri2]])
                    depth2 = len(pathList)
                    
                    G.add_node(node1,color='#b94431')
                    G.node[node1]['size']=depth1
                    G.node[node1]['URI']=uri1
                    print "START","added",node1
                    
                    G.add_node(node2,color='#b94431')
                    G.node[node2]['size']=depth2
                    G.node[node2]['URI']=uri2
                    print "START","added",node2                            

    def drawLCS(nodeList):
        global path,dicto,pathList,G,LCS        
        for i in range(len(nodeList)):
            currentURI = nodeList[i]
            for j in range(i+1,len(nodeList)):
                otherURI = nodeList[j]
                findLCS(currentURI,otherURI)
                if LCS[0][0] != 0:
                    LCSnode = dicto[LCS[0][0]]
                    if G.has_node(LCSnode) is False:
                        G.add_node(LCSnode,color='#da991c')
                        print "\nLCS: added",LCSnode
                        
    def drawBFS(nodeList):
        global path
        path = []
        if len(nodeList) > 0:
            for i in range(len(nodeList)):
                node1 = nodeList[i]
                for j in range(i+1,len(nodeList)):
                    node2 = nodeList[j]
                    if node1 == node2:
                        # Same node, no need for BFS
                        G.add_node(dicto[node1],color='#333333')
                        print "\nNode1 = Node2!"
                        print "BFS: added",node1
                    else:
                        # Different node, find parents
                        findParents([[node2]])
                        if len(pathList) > 1:
                            parent2 = pathList[-1][-1][-1]
                        else:
                            parent2 = pathList[0][0]
                        findParents([[node1]])
                        if len(pathList) > 1:
                            parent1 = pathList[-1][-1][-1]
                        else:
                            parent1 = pathList[0][0]
                            
                        if parent1 == parent2:
                            # Same cluster
                            path=[]
                            print "BFS Trying:",node1,node2
                            pathFinder(node1,node2)
                            print "BFS Finished\n"
                            for i in range(len(path)):
                                nodeLeft=dicto[path[i][0]]
                                nodeRight=dicto[path[i][2]]

                                if path[i][1] == 'is a':
                                    edge=path[i][1]
                                else:
                                    edge=dicto[path[i][1]]
                                if G.has_node(nodeLeft) is False:
                                    G.add_node(nodeLeft,color='#333333')
                                    print "\nBFS: added",nodeLeft
                                if G.has_node(nodeRight) is False:                                    
                                    G.add_node(nodeRight,color='#333333')
                                    print "\nBFS: added",nodeRight
                                G.add_edge(nodeLeft,nodeRight,color='#b94431')

                        else:
                            # Different cluster, through root
                            print "BFS through root"
                            print "Trying:",node1,node2
                            print "Node1->Parent",node1,parent1
                            if node1 == parent1:
                                G.add_node(dicto[node1],color="#333333")
                                G.add_edge(dicto[node1],'Thing')
                                print "\nBFS: added",dicto[node1]
                            else:
                                pathFinder(node1,parent1)
                                for i in range(len(path)):
                                    nodeLeft=dicto[path[i][0]]
                                    nodeRight=dicto[path[i][2]]
                                    
                                    if path[i][1] == 'is a':
                                        edge=path[i][1]
                                    else:
                                        edge=dicto[path[i][1]]

                                    if G.has_node(nodeLeft) is False:
                                        G.add_node(nodeLeft,color='#333333')
                                        print "\nBFS: added",nodeLeft
                                    if G.has_node(nodeRight) is False:                                    
                                        G.add_node(nodeRight,color='#333333')
                                        print "\nBFS: added",nodeRight
                                    G.add_edge(nodeLeft,nodeRight,color='#b94431')

                            if node2 == parent2:
                                G.add_node(dicto[node2],color="#333333")
                                G.add_edge(dicto[node2],'Thing')
                                print "\nBFS: added",dicto[node2]
                            else:
                                pathFinder(node2,parent2)
                                for i in range(len(path)):
                                    nodeLeft=dicto[path[i][0]]
                                    nodeRight=dicto[path[i][2]]
                                    if path[i][1] == 'is a':
                                        edge=path[i][1]
                                    else:
                                        edge=dicto[path[i][1]]
                                    if G.has_node(nodeLeft) is False:
                                        G.add_node(nodeLeft)
                                        print "\nBFS: added",nodeLeft
                                    if G.has_node(nodeRight) is False:
                                        G.add_node(nodeRight)
                                        print "\nBFS: added",nodeRight
                                    G.add_edge(nodeLeft,nodeRight,color='#b94431')

    def drawParents(nodeList):
        global path,dicto,pathList,G,LCS
        for i in range(len(nodeList)):
            currentURI = nodeList[i]
            findParents([[currentURI]])
            CSpec = len(pathList)
            for i in range(1,len(pathList)):
                for j in range(len(pathList[i])):
                    prevNode = dicto[pathList[i][j][0]]
                    node = dicto[pathList[i][j][1]]
                    if G.has_node(prevNode) is False:
                        G.add_node(prevNode,color='#333333')
                        print "\nParents: added",prevNode
                    if G.has_node(node) is False:
                        G.add_node(node,color='#333333')
                        print "\nParents: added",node
                    if G.has_node(node) is True and i == CSpec-1:
                        G.add_edge(node,'Thing')
                    G.add_edge(prevNode,node)

    drawLCS(URIlist)
    drawBFS(URIlist)    
    drawParents(URIlist)
    drawStart(URIlist)
    
    data = json_graph.node_link_data(G)
    s = json.dumps(data)
    print '\nJSON:'
    print s

    nx.write_gexf(G,'file.gv')
    #os.system("gv\\bin\\dot.exe -Tpng -ograph.png file.gv")
    #print "Created graph.png"

def measureSim(node1,node2):
    "Leacock & Chodorow's semantic similarity measure"
    global path,pathlength
    if node1 != node2:
        findParents([[node1]])
        if len(pathList) > 1:
            parent1 = pathList[-1][-1][-1]
        else:
            parent1 = pathList[-1][-1]
            
        findParents([[node2]])
        if len(pathList) > 1:
            parent2 = pathList[-1][-1][-1]
        else:
            parent2 = pathList[-1][-1]
            
        if parent1 == parent2:
            # print "Both nodes in same cluster"
            pathFinder(node1,node2)
            semDist = -math.log((float(pathlength+1)) / float(30))
            return semDist
        else:
            # print "Nodes from different clusters, via root"
            if node1 != parent1:
                pathFinder(node1,parent1)
                length1 = pathlength
            else:
                # print "node1 == parent1"
                length1 = 1
            if node2 != parent2:
                pathFinder(node2,parent2)
                length2 = pathlength
            else:
                # print "node2 == parent2"
                length2 = 1
            length = length1+length2+1
            semDist = -math.log((float(length)) / float(30))
            return semDist
    else:
        # print "node1 == node2"
        semDist = -math.log((float(1)) / float(30))
        return semDist

def drawNetwork(nodes1,nodes2):
    CG = nx.Graph()
    c1 = 'red'
    c2 = 'blue'
    # Draw list1 + list2
    nodesAll = [nodes1,nodes2]
    for x in range(len(nodesAll)):
        nodes = nodesAll[x] 
        for i in range(len(nodes)):
            uri1 = nodes[i]
            if len(uri1)>0:
                label1 = dicto[uri1]
            else:
                break
            for j in range(i+1,len(nodes)):
                uri2 = nodes[j]
                if len(uri2)>0:
                    label2 = dicto[uri2]
                else:
                    break
                    
                similarity = measureSim(uri1,uri2)
                
                findParents([[uri1]])
                depth1 = len(pathList)
                if len(pathList) > 1:
                    parent1 = pathList[-1][-1][-1]
                else:
                    parent1 = pathList[-1][-1]            
                CG.add_node(label1)
                CG.node[label1]['color']=c1
                CG.node[label1]['size']=depth1
                CG.node[label1]['URI']=uri1
                CG.node[label1]['type']=dicto[parent1]            

                findParents([[uri2]])
                if len(pathList) > 1:
                    parent2 = pathList[-1][-1][-1]
                else:
                    parent2 = pathList[-1][-1]              
                depth2 = len(pathList)
                CG.add_node(label2)
                CG.node[label2]['color']=c1
                CG.node[label2]['size']=depth2
                CG.node[label2]['URI']=uri2
                CG.node[label2]['type']=dicto[parent2]

                CG.add_edge(label1,label2)
                CG.edge[label1][label2]['width']=round(similarity,5)
                CG.edge[label1][label2]['label']= label1 + ' - ' + label2 + ": " + str(round(similarity,3))

def compareGraph(nodes1,nodes2):
    global CG
    simList = []
                
    # Compare both lists
    for i in range(len(nodes1)):
        temp = []
        uri1 = nodes1[i]
        if len(uri1)>1:
            label1 = dicto[uri1]
        else:
            break
        for j in range(len(nodes2)):
            uri2 = nodes2[j]
            if len(uri2)>1:
                label2 = dicto[uri2]
            else:
                break

            similarity = measureSim(uri1,uri2)
            temp.append([similarity,uri1,uri2])
            
        temp = sorted(temp,reverse=True)
        if len(temp)>0:
            simList.append(temp[0])
        else:
            simList.append([0,'-','-'])
            
    for i in range(len(nodes2)):
        temp2 = []
        uri1 = nodes2[i]
        if len(uri1)>1:
            label1 = dicto[uri1]
        else:
            break
        for j in range(len(nodes1)):
            uri2 = nodes1[j]
            if len(uri2)>1:
                label2 = dicto[uri2]
            else:
                break

            similarity = measureSim(uri1,uri2)
            temp2.append([similarity,uri2,uri1])

        temp2 = sorted(temp2,reverse=True)
        if len(temp2)>0:
            if temp2[0] not in simList:
                simList.append(temp2[0])
        else:
            simList.append([0,"-","-"])
    
    simFile = open('similarity.csv','w')
    for i in range(len(simList)):
        uri1 = simList[i][1]
        uri2 = simList[i][2]
        if len(uri1)>1:
            label1 = dicto[uri1]
        else:
            break
        if len(uri2)>1:
            label2 = dicto[uri2]
        else:
            break

        findParents([[uri1]])
        depth1 = len(pathList)
        CG.add_node(label1)
        CG.node[label1]['color']='red'
        CG.node[label1]['size']=depth1
        CG.node[label1]['URI']=uri1

        findParents([[uri2]])
        depth2 = len(pathList)
        CG.add_node(label2)
        CG.node[label2]['color']='blue'
        CG.node[label2]['size']=depth2
        CG.node[label2]['URI']=uri2

        CG.add_edge(label1,label2)
        CG.edge[label1][label2]['width']=round(similarity,5)
        CG.edge[label1][label2]['weight']=round(similarity,5)            
        CG.edge[label1][label2]['label']= label1 + ' - ' + label2 + ": " + str(round(similarity,3))
        
        simFile.write('"' + str(simList[i][0]) + '";"' + simList[i][1] + '";"' + simList[i][2] + '"\n')
    simFile.close()

def clusterGraph(list_of_graphs):
    global CG
    CG = nx.Graph()
    for i in range(len(list_of_graphs)):
        graph1 = list_of_graphs[i]
        for j in range(i+1,len(list_of_graphs)):
            graph2 = list_of_graphs[j]
            compareGraph(graph1,graph2)
    '''
    data = json_graph.node_link_data(CG)
    s = json.dumps(data)
    log = open('json.txt','w')
    log.write(s)
    log.close()
    nx.write_gexf(CG,'cluster.gexf')
    '''

def csvToNodes(directory):
    files = os.listdir(directory)
    finalList = []  
    for i in range(len(files)):
        csvtje = csv.reader(open(str(directory) + str(files[i]),'rb'),delimiter=';',quotechar='"')
        print files[i]
        docList = []
        for line in csvtje:
                uriList=[]
                temp = line[1].split(',')
                for j in range(len(temp)):
                    if len(temp)>0:
                        uriList.append(str(temp[j]).replace(' ',''))
                docList.append(uriList)
        finalList.append(docList)
    print len(finalList)
    return finalList

def getDepth(list):
    resultList = []
    newList=[]
    for i in range(len(list)):
        for j in range(len(list[i])):
            if 'http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#' in list[i][j]:
                findParents([[list[i][j]]])
                list[i][j] = len(pathList)
    for i in range(len(list)):
            total = 0
            avg = 0
            for j in range(len(list[i])):
                if type(list[i][j]) == int:
                    total += int(list[i][j])
                else:
                    total += 0
            avg = float(total) / float(len(list[i]))
            resultList.append(avg)
    number = 0
    for i in range(len(resultList)):
        number += resultList[i]
    print number/len(resultList)

def getSim(directory):
    finalList = []
    allFiles = os.listdir(directory)
    files = []
    for i in range(len(allFiles)):
        if '.csv' in allFiles[i]:
            files.append(allFiles[i])
    for i in range(0,len(files),8):
        currentAlgo = files[i:i+8]
        similarityList = []
        for k in range(len(currentAlgo)):
            csvtje = csv.reader(open(str(directory) + str(currentAlgo[k]),'rb'),delimiter=';',quotechar='"')
            for line in csvtje:
                similarityList.append(line[0])
        
        # Median
        if len(similarityList) > 0:
            values = sorted(similarityList)
            if len(values) % 2 == 1:
                median = values[(len(values)+1)/2-1]
            else:
                lower = float(values[len(values)/2-1])
                upper = float(values[len(values)/2])
                median = (float(lower + upper)) / 2
        else:
            median = 0.0

        # Mean
        sumNr = 0
        if len(similarityList) > 0:
            for j in range(len(similarityList)):
                sumNr += float(similarityList[j])
            average = float(sumNr) / float(len(similarityList))
        else:
            average = 0.0

        # Standard deviation
        sumNr2 = 0
        if len(similarityList) > 0:
            for j in range(len(similarityList)):
                sumNr2 += float(float(float(similarityList[j])-float(average))*float(float(similarityList[j])-float(average)))
            stdev = math.sqrt(float(sumNr2)/float(len(similarityList)))
        else:
            stdev = 0.0
            
        finalList.append([str(files[i]),median,average,stdev])
            
    log = open('similarityStuff.csv','w')
    log.write('"source";"median";"mean";"standard deviation"\n')
    log.close()
    for k in range(len(finalList)):
        # print '"' + str(finalList[i]) + '";"' + str(finalList[i+1]) + '";"' + str(finalList[i+2]) + '";"' + str(finalList[i+3]) + '"\n'
        log = open('similarityStuff.csv','a')
        log.write('"' + str(finalList[k][0]) + '";"' + str(finalList[k][1]) + '";"' + str(finalList[k][2]) + '";"' + str(finalList[k][3]) + '"\n')
        log.close()

finalList = csvToNodes("log\\expert\\")
resp1 = finalList[0]
resp2 = finalList[1]
resp3 = finalList[2]
print "Filled resp1, resp2 & resp3"
algoList = csvToNodes("log\\DEF-TF\\")
print "Filled algo1-24"

def clusterAll(algolist,resplist):
    for i in range(len(algolist)):
        currentAlgo = algolist[i]
        for j in range(len(currentAlgo)):
            clusterGraph([currentAlgo[j],resplist[j]])
            '''
            os.rename('json.txt', "json" + str(i) + "." + str(j) + '.txt')
            os.rename('cluster.gexf', "cluster" + str(i) + "." + str(j) + '.gexf')
            '''
            os.rename('similarity.csv','similarity' + str(i) + "." + str(j) + '.csv')

def clusterMan(resplist1,resplist2):
    for i in range(len(resplist1)):
            clusterGraph([resplist1[i],resplist2[i]])
            # os.rename('json.txt', "json" + str(i) + '.txt')
            # os.rename('cluster.gexf', "cluster" + str(i) + '.gexf')
            os.rename('similarity.csv','similarity' + str(i) + '.csv')
            
def showPath(list,start,target):
    global path,dicto
    GR = nx.Graph()
    
    for x in range(len(list),0,-1):
            hop = list[x-1]
            for i in range(len(hop)):
                if len(hop[i]) == 3:
                    leftNode = hop[i][0]
                    rightNode = hop[i][2]
                    GR.add_node(leftNode)
                    GR.add_node(rightNode)
                    GR.add_edge(leftNode,rightNode)
                else:
                    GR.add_node(hop[i])

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

        # X is a URI
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
            if "part_of" in x["p"]["value"].lower():
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
            if "part_of" in x["p"]["value"].lower():            
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
    global LCS,pathList
    LCS = []
    LCS = [[findCommonParents(URI1,URI2)]]
    if LCS[0][0] != 0:
        findParents(LCS)
        print "LCS: " + str(dicto[pathList[0][0]]),"(" + str(dicto[URI1]) + "," + str(dicto[URI2]) + "): "
    else:
        print "No LCS"

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
