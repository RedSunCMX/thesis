from SPARQLWrapper import SPARQLWrapper,JSON
from pprint import pprint

context = []
queue = []
visited = []

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

def BFS(URI1,URI2,q):
    global queue,visited
    q.enqueue([URI1])
    
    while q.IsEmpty() == False:
        curr_path = q.dequeue()
        queue.append(curr_path)
        for i in range(len(curr_path)):
            if len(curr_path) > 1:
                node1 = curr_path[i][0]
                node2 = curr_path[i][2]
                if node1 == URI2:
                    print "\nFound a link in hop",len(queue)-1
                    showPath(queue,URI1,URI2)
                if node2 == URI2:
                    print "\nFound a link in hop",len(queue)-1
                    showPath(queue,URI1,URI2)
                if node1 not in visited and 'http://www.w3.org/2002/07/owl#Class' not in node1:
                    node = node1
                    visited.append(node)
                    getNodes(node,URI2)
                    q.enqueue(context)
                else:
                    # node1 has been visited or is owl:Class
                    # print node1,"has been visited! Trying node2"
                    if 'http://www.w3.org/2002/07/owl#Class' not in node2 and node2 not in visited:
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

def qPath(URI,URI2,hops):
    sparql = SPARQLWrapper('http://dvdgrs-900:8080/openrdf-sesame/repositories/cyttron')
    if hops == 3:
        querystring="""
            SELECT DISTINCT ?p ?s
            WHERE {
            <" + str(URI) + "> ?p ?s .
            ?s ?p2 ?o .
            ?o ?p3 ?o2 .
            FILTER (isURI(?s )) }"""
    # print querystring    

def showPath(list,start,target):
    newList=[]
    for x in range(len(list),0,-1):
        if x-1 > 1:
            hop = list[x-1]
            print x-1,
            for i in range(len(hop)):
                leftNode = hop[i][0]
                rightNode = hop[i][2]
                if leftNode == target:
                    print hop[i]
                    newList.append(hop[i])
                    target = rightNode
                    break
                if rightNode == target:
                    print hop[i]
                    newList.append(hop[i])
                    target = leftNode
                    break
        if x-1 == 1:
            hop = list[x-1]
            print x-1,
            for i in range(len(hop)):
                leftNode = hop[i][0]
                rightNode = hop[i][2]
                if leftNode == start and rightNode == target:
                    print hop[i]
                    newList.append(hop[i])
                    return newList
                if rightNode == start and leftNode == target:
                    print hop[i]
                    newList.append(hop[i])
                    return newList
            

def getNodes(URI,URI2):
    global context
    context=[]
    sparql = SPARQLWrapper('http://dvdgrs-900:8080/openrdf-sesame/repositories/cyttron')
    querystring="SELECT DISTINCT ?p ?s WHERE { <" + str(URI) + "> ?p ?s . FILTER (isURI(?s )) }"
    # print querystring
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context.append([URI,x["p"]["value"],x["s"]["value"]])
    querystring="SELECT DISTINCT ?o ?p WHERE { ?o ?p <" + str(URI) + "> . FILTER (isURI(?o )) }"
    # print querystring
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context.append([x["o"]["value"],x["p"]["value"],URI])
    return context
'''
    print len(context),"neighbouring nodes"
    print context
    
    for i in range(len(context)):
        node1 = context[i][0]
        node2 = context[i][1]
        if node1 == URI:
            print node2
        else:
            print node1
'''
