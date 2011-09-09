from SPARQLWrapper import SPARQLWrapper,JSON

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
                if node1 == URI2:
                    print "\nFound a link!"
                    showPath(queue,URI1,URI2)
                if node2 == URI2:
                    print "\nFound a link!"
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

def showPath(list,start,target):
    newList=[]
    for x in range(len(list),0,-1):
        if x-1 > 1:
            hop = list[x-1]
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
                    print newList                    
                if rightNode == start and leftNode == target:
                    print hop[i]
                    newList.append(hop[i])
                    print newList

def getNodes(URI,URI2):
    global context
    context=[]
    sparql = SPARQLWrapper('http://dvdgrs-900:8080/openrdf-sesame/repositories/cyttron')
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
        exit

def findCommonParents(URI1,URI2):
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
                        print "[findCommonP]\t","Result1[" + str(i) + "][" + str(i2) +"]",
                        print "matches with result2[" +str(j) + "][" + str(j2) + "]"
                        print "[findCommonP]\t",result1[i][i2]
                        parent1 = result1
                        parent2 = result2
    return parent1,parent2

def findMultiParent(URIlist):
    global bigList
    n = len(URIlist)
    for i in range(n):
        for j in range(i+1,n):
            print str(URIlist[i]),"-",str(URIlist[j])
            findCommonParents(URIlist[i],URIlist[j])
            bigList.append([parent1,parent2])
