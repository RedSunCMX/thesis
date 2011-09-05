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
        print "Current path:",curr_path
        for i in range(len(curr_path)):
            if len(curr_path) > 1:
                node1 = curr_path[i][0]
                node2 = curr_path[i][1]
                if node1 == URI2:
                    print "FOUND THAT SHIT!"
                    return q
                    exit
                if node2 == URI2:
                    print "FOUND THAT SHIT!"
                    return q
                    exit
                if node1 not in visited and 'http://www.w3.org/2002/07/owl#Class' not in node1:
                    print "node1 has not been visited, doing so now!"
                    node = node1
                    print "\nNode:",node   
                    visited.append(node)
                    print "Visited:",visited
                    getNodes(node)
                    q.enqueue(context)
                    getNodes(node)
                else:
                    # node1 has been visited or is owl:Class
                    print node1,"has been visited! Trying node2"
                    if 'http://www.w3.org/2002/07/owl#Class' not in node2 and node2 not in visited:
                        print "node2 has not been visited, doing so now!"
                        node = node2
                        print "\nNode:",node                    
                        visited.append(node)
                        print "Visited:",visited
                        getNodes(node)
                        q.enqueue(context)
                    else:
                        print "node2 has been visited, need to go to next path"
                        i+=1
            else:
                node = curr_path[0]
                print "\nNode:",node
                visited.append(node)
                print "Visited:",visited
                getNodes(node)
                q.enqueue(context)


'''
        if node in visited:
            print "Node has been visited, try another"
            # jump back to first for-loop
            curr_path = q.dequeue()
        print "Node:",node
        visited.append(node)
        print "Visited:",visited
        getNodes(node)
        q.enqueue(context)
'''        
def getNodes(URI):
    global context
    print ""
    context=[]
    sparql = SPARQLWrapper('http://dvdgrs-900:8080/openrdf-sesame/repositories/cyttron')
    querystring="SELECT DISTINCT ?s WHERE { <" + str(URI) + "> ?p ?s . FILTER (isURI(?s )) }"
    # print querystring
    sparql.setReturnFormat(JSON)
    sparql.addCustomParameter("infer","false")
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context.append([URI,x["s"]["value"]])
    querystring="SELECT DISTINCT ?o WHERE { ?o ?p <" + str(URI) + "> . FILTER (isURI(?o )) }"
    # print querystring
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        context.append([x["o"]["value"],URI])
    print len(context),"neighbouring nodes"
    #pprint(context)
    return context
