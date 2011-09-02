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
        #print "Current path:",curr_path
        for i in range(len(curr_path)):
            if len(curr_path) > 1:
                if curr_path[i] not in visited:
                    if curr_path[i][0] not in visited:
                        node = curr_path[i][0]
                    else:
                        node = curr_path[i][1]
            else:
                node = curr_path[0]
        print "Node:",node
        visited.append(node)
        print "Visited:",visited
        getNodes(node)
        q.enqueue(context)
        
def getNodes(URI):
    global context
    print ""
    context=[]
    sparql = SPARQLWrapper('http://dvdgrs-laptop:8080/openrdf-sesame/repositories/Cyttron_DB')
    querystring="SELECT DISTINCT ?s WHERE { <" + str(URI) + "> ?p ?s . FILTER (isURI(?s ))  }"
    print querystring
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context.append([URI,x["s"]["value"]])
    querystring="SELECT DISTINCT ?o WHERE { ?o ?p <" + str(URI) + "> . FILTER (!isURI(?o )) }"
    print querystring
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context.append([x["o"]["value"],URI])
    print len(context),"neighbouring nodes"
    return context
