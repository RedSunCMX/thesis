# -*- coding: utf-8 -*-
import signal
import apscheduler
from apscheduler.scheduler import Scheduler
import sched, time
import twitter
import nltk
from SPARQLWrapper import SPARQLWrapper,JSON
from nltk.tokenize import word_tokenize
from nltk import pos_tag
from nltk.corpus import wordnet
import random
import logging
logging.basicConfig()

endpoint = "http://dbpedia.org/sparql"
sparql = SPARQLWrapper(endpoint)
sparql.setReturnFormat(JSON)

found = []
URI = ""
match=""
t = ""

replyLog = open('/home/dvdgrs/Dropbox/lastmentionID.txt','r')

iup=0
idown=0

propCounter = 0

pathList=[]

newID=""
label = []
conceptSearch = []
pos=[]

api = twitter.Api(consumer_key='x',consumer_secret='x',access_token_key='x',access_token_secret='x')
ver = api.VerifyCredentials()
print "logged in as",ver.screen_name
friends = api.GetFriends()
print ver.screen_name,"has",len(friends),"friends:"
for friend in friends:
    print friend.screen_name,

class Tweet:
    def __init__ (self):
        self.name = concept[1]

        self.concept = concept
        self.conceptString = ""
        self.conceptList = []

        self.instance = []

        self.subClass = []
        self.subList = []
        
        self.propList = []
        self.property = []

        self.valueList = []
        self.value = []

        self.domain = []

        self.finalResult = ""
        self.path = []
		
def startTwitter():
    api = twitter.Api(consumer_key='x',consumer_secret='x',access_token_key='x',access_token_secret='x')
    ver = api.VerifyCredentials()
    print "logged in as",ver.screen_name
    friends = api.GetFriends()
    print ver.screen_name,"has",len(friends),"friends:"
    for friend in friends:
        print friend.screen_name,

def randomFriend():
    print ""
    global pos
    rand = int(random.randrange(len(friends)))
    chosenFriend = friends[rand]
    print "Picked",str(chosenFriend.screen_name) + ":",chosenFriend.status.text
    words = nltk.word_tokenize(chosenFriend.status.text)
    pos = nltk.pos_tag(words)

def getConcepts():
    print ""
    global concept
    concept = []
    querystring = 'select distinct ?concept ?label where {?concept rdfs:isDefinedBy <http://dbpedia.org/ontology/> . ?concept rdfs:label ?label . ?x a ?concept . filter( langMatches( lang(?label), "en")||(!langMatches(lang(?label),"*")) )}'
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        concept.append([x["concept"]["value"],x["label"]["value"]])
    print "Retrieved",len(concept),"concepts."

def nounSyn():
# Retrieve nouns from tweet
    print ""
    global URI, found
    found = []
    list=[]
    n=0
    tag_prefix = 'NN'
    for i in range(len(pos)):
        tag = pos[i][1]
        word = pos[i][0].rstrip('.,:;')
        # if word is a NOUN, query DBPedia for its occurrence
        if tag.startswith(tag_prefix):
            print word
            querystring = 'SELECT DISTINCT ?URI WHERE { ?URI ?p "' + word.rstrip('.,:";') + '" . }'
            print querystring
            sparql.setQuery(querystring)
            results = sparql.query().convert()
            for x in results["results"]["bindings"]:
                if 'dbpedia.org' in x["URI"]["value"]:
                    found.append(x["URI"]["value"])
                    print x["URI"]["value"]
    found = dict.fromkeys(found)
    found = found.keys()
    found.sort()
    print "\n",len(found),"concepts found.\n"
    URI = found
    return URI

def randomTweet():
    global t
    print ""
    t = Tweet()
    rand = int(random.randrange(len(concept)))
    t.concept = concept[rand]
    print "[randomTweet]\t",t.concept
    print "[randomTweet]\t","Picked",t.concept[1]
    findInst(t)
    status = api.PostUpdate(t.finalResult)
    print "[randomTweet]\t",t.finalResult

def tweet(conceptstring):
    print ""
    t = Tweet
    t.conceptString = conceptstring
    findConcept(t)
    if len(t.conceptList)>0:
        rand = int(random.randrange(len(t.conceptList)))
        t.concept = [t.conceptList[rand][0],str(conceptstring)]
        print "[tweet]\t\t",t.concept
        findInst(t)
    else:
        print "[tweet]\t\t","I don't know any concept named " + str(conceptstring) + "."
        t.finalResult=''
        exit
    if len(t.finalResult) > 0:
        print t.finalResult
        status = api.PostUpdate(t.finalResult)
    else:
        exit

def conceptMatch(tweet):
    "Input string, output [label,uri]-thing (in match)"
    print ""
    global concept,match
    countConcept = int    
    found=[]
    URIlist=[]
    count=0
    for i in range(len(concept)):
        currentConcept = str(concept[i][1]).lower()
        currentURI = str(concept[i][0])
        countConcept = tweet.count(currentConcept)
        count += countConcept
        if countConcept > 0:
            found.append([currentURI,currentConcept])
    if count == 1:
        print "[conceptMatch]\t","Found",count,"concept:",found
        match = found[0]
        print "[conceptMatch]\t","Picked",match
    elif count > 1:
        print "[conceptMatch]\t","Found",count,"concepts.",found
        for i in range(len(found)):
            URIlist.append(found[i][0])
        URIlist = [URIlist]
        print URIlist
        # Heavy WIP
        for i in range(len(URIlist[0])):
            if i > 0:
                print "[conceptMatch]\t","Comparing:",URIlist[0][0],"to:",URIlist[0][i]
                findCommonParents(URIlist[0][0],URIlist[0][i])
    elif count == 0:
        match = ""
        print "[conceptMatch]\t",count,"concepts found :(."

def findConcept(t):
# finds a concept from a conceptString in Tweet-instance
    print ""
    t.conceptList = []
    print "[findConcept]\t","findConcept('" + str(t.conceptString) + "')"
    print "[findConcept]\t","Looking for concept: ",str(t.conceptString)
    querystring='SELECT DISTINCT ?o WHERE { ?o rdfs:label "' + str(t.conceptString) + '" .}'
    # print "[findConcept]\t",querystring
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        if 'dbpedia.org' in x["o"]["value"]:
            t.conceptList.append([x["o"]["value"],t.conceptString])
    if len(t.conceptList) > 0:
        exit
    else:
        print "[findConcept]\t","No concept called",t.conceptString,"found :(...\n"
        exit

def findParents(URI):
    # In: list with list(s) of URIs [[URI1,URI2,URI3]]
    global iup, pathList
    list_out=[]
    iup += 1
    # print "[findParents]\t","Hop",iup,"found",len(URI[iup-1]),"nodes"
    for i in range(len(URI[iup-1])):
        querystring = 'SELECT DISTINCT ?super WHERE { <' + URI[iup-1][i] + '> rdfs:subClassOf ?super . FILTER isURI(?super) }'
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        for x in results["results"]["bindings"]:
            if 'dbpedia.org' in x["super"]["value"]:
                list_out.append(x["super"]["value"])
    list_out = list(set(list_out))
    if len(list_out) > 0:
        URI.append(list_out)
        findParents(URI)
    else:
        # print "[findParents]\t","Reached the top!"
        print "[findParents]\t",URI[0][0]
        print "[findParents]\t","Hop | Path:"
        for i in range(len(URI)):
            print "[findParents]\t",i,"  |",URI[i]
        iup=0
        pathList = URI
        exit

def findChildren(URI):
    print ""
    global idown, pathList
    list_out=[]
    idown += 1
    print "Hop",idown,"found",len(URI[idown-1]),"nodes"
    rand = int(random.randrange(len(URI[idown-1])))
    querystring = 'SELECT DISTINCT ?sub WHERE { ?sub ?p <' + URI[idown-1][rand] + '> . FILTER isURI(?sub) }'
    print querystring
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        list_out.append(x["sub"]["value"])
    list_out = list(set(list_out))
    if len(list_out) > 0:
        URI.append(list_out)
        findChildren(URI)
    else:
        print "Reached the bottom!"
        print "\nHop | Path:"
        for i in range(len(URI)):
            print i,"  |",URI[i]
        print '\n'
        idown=0
        pathList = URI
        exit

def findCommonParents(URI1,URI2):
    # Input URI strings, output common Parent
    print ""
    URI1 = [[URI1]]
    URI2 = [[URI2]]
    iup = 0
    global result1,result2,pathList

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
                        print "[findCommonP]\t","matches with result2[" +str(j) + "][" + str(j2) + "]"
                        print "[findCommonP]\t",result1[i][i2]
                        print "[findCommonP]\t",result2[j][j2]
    # Display
    return result1,result2

def exploreContext(URI):
# Retrieve all relations a node has with its surroundings, and its surroundings to the node.
    print ""
    querystring="SELECT DISTINCT ?p WHERE { <" + str(URI) + "> ?p ?s . }"
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        print x["p"]["value"]
    querystring="SELECT DISTINCT ?p WHERE { ?o ?p <" + str(URI) + "> . }"
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        print x["p"]["value"]
		
def checkMentions():
    print ""
    global newID,replyLog,concept,randomMatch
    found=[]
    replyLog = open('/home/dvdgrs/Dropbox/lastmentionID.txt','r')
    last_id = replyLog.read()
    replyLog.close()
    countConcept = int
    count = 0
    print "[checkMentions]\t",last_id
    mentions = api.GetMentions(since_id=last_id)
    for mention in mentions:
        print "[checkMentions]\t",mention.GetUser().GetScreenName(),"mentioned me! ID:",mention.GetId()
        mentionUser = str(mention.GetUser().GetScreenName())
        mentionTweet = str(mention.text).lower()
        print "[checkMentions]\t",mentionTweet
        new_id = mention.GetId()
        # Have mention!
        if mentions > 0:
            conceptMatch(mentionTweet)
            # Create ID for reply function
            newID = str(new_id)

            # No match!
            if match == "":
                print"[checkMentions]\t","No match found. Replying with random message..."
                
                messageList = ["I don't know what you're talking about...","Could you rephrase that?","Yes","Nope","What?","Ask @dvdgrs","If you say so... ;)","no idea!","sure","I don't know. Try one of these: http://mappings.dbpedia.org/server/ontology/classes"]
                rand = int(random.randrange(len(messageList)))
                message = messageList[rand]
                name = "@" + mentionUser
                answer = str(name)+ " " + str(message)
                status = api.PostUpdate(answer,newID)
                print "[checkMentions]\t",status
                
            # Match!
            else:
                reply(mentionUser,match)

            # Write newID to the log as last replied to.
            replyLog = open('/home/dvdgrs/Dropbox/lastmentionID.txt','w')
            replyLog.write(newID)
            replyLog.close()

def reply(nick,conceptlist):
    print ""
    # reply receives a concept from checkMentions, posts a reply along with newID
    global finalResult,newID
    t = Tweet()
    t.concept = conceptlist
    findInst(t)
    name = "@" + nick
    reply = str(name)+ " " + str(t.finalResult)
    if len(t.finalResult) > 0:
        print "[reply]\t\t",reply
        status = api.PostUpdate(reply,newID)
    else:
        print "[reply]\t\t","Nothing to post..."
        exit

def mention(nick,string):
    print ""
    # Same as reply, however it looks up the concept-string first.
    global concept,conceptSearch
    conceptSearch = []
    print "[mention]\t","reply(" + str(nick) + "," + str(string) + ")"
    t = Tweet
    t.conceptString=string
    findConcept(t)
    if len(t.conceptList) > 0:
        print "[mention]\t","Received a concept from the findConcept function:"
        rand = int(random.randrange(len(t.conceptList)))
        t.concept = t.conceptList[rand]
        print "[mention]\t",t.concept
    else:
        print "[mention]\t","No concept received from findConcept, picking a random concept:"
        rand = int(random.randrange(len(concept)))
        t.concept = concept[rand]
        print "[mention]\t",t.concept
    list = []
    findInst(t)
    name = "@" + nick
    reply = str(name)+ " " + str(t.finalResult)
    print "[mention]\t",reply
    if len(t.finalResult) > 0:
        status = api.PostUpdate(reply,None)
    else:
        print "[mention]\t","Nothing to post..."
        exit

def findThing(string):
    print ""
    querystring = 'SELECT ?x WHERE { ?x rdfs:label ?label . ?x a ?y . FILTER (regex(?label, "' + string + '")) . }'
    print querystring
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results:
        print x

def checkPublic():
    print ""
    global newID,replyLog
    users = api.GetFollowers()
    text = [[user.GetScreenName(),user.status.text,user.status.id] for user in users]
    
    nick = text[0][0]
    tweet = text[0][1]
    newID = text[0][2]

    conceptMatch(tweet)
    
    if match == "":
        print "Nothing found"
    else:
        reply(nick,match)

def findInst(t):
    # Accepts [URI,label] DBPedia-concept, executes findProp
    print ""
    list=[]
    print "[findInst]\t","Seed:",t.concept
    # Find instances of seed-class
    querystring="SELECT DISTINCT ?instance ?label WHERE { ?instance a <" + str(t.concept[0]) + '> . ?instance rdfs:label ?label . filter( langMatches( lang(?label), "en")||(!langMatches(lang(?label),"*")) )}'
    # print "[findInst]\t",querystring
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        list.append([x["instance"]["value"],x["label"]["value"]])
    if len(list) > 0:
        print "[findInst]\t","Has",len(list),"instances."
        rand = int(random.randrange(len(list)))
        t.instance = list[rand]
        print "[findInst]\t","Instance:",t.instance[1]
        findProp(t)
    else:
        print "[findInst]\t","No instances found. Trying subclass..."
        findSubClass(t)

def findSubClass(t):
    print ""
    t.subList = []
    querystring="SELECT DISTINCT ?subClass ?label WHERE { ?subClass rdfs:subClassOf <" + str(t.concept[0]) + '> . ?subClass rdfs:label ?label . filter( langMatches( lang(?label), "en")||(!langMatches(lang(?label),"*")) )}'
    # print "[findSub]\t",querystring
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        t.subList.append([x["subClass"]["value"],x["label"]["value"]])
    if len(t.subList) == 0:
        print "[findSub]\t","Nothing found. Exit."
        t.finalResult=""
        exit
    else:
        print "[findSub]\t","Found",len(t.subList),"subClasses!"
        rand = int(random.randrange(len(t.subList)))
        t.concept = t.subList[rand]
        print "[findSub]\t",t.concept
        findInst(t)

def findProp(t):
    # Accepts findInst input, returns finalResult
    print ""
    t.propList = []
    global propCounter,voorzetsel
    # Voorzetsel ding
    if str(t.concept[1])[0] == 'a' or str(t.concept[1])[0] == 'e' or str(t.concept[1])[0] == 'o' or str(t.concept[1])[0] == 'i' or str(t.concept[1])[0] == 'u':
        voorzetsel = "an"
    else:
        voorzetsel = "a"
    # Return properties of given instance
    querystring="""SELECT DISTINCT ?prop ?propLabel WHERE {<""" + str(t.instance[0]) + """> ?prop ?obj . ?prop a rdf:Property . ?prop rdfs:label ?propLabel . FILTER( (langMatches(lang(?propLabel),'en'))||(!langMatches(lang(?propLabel),"*")) ) }"""
    # print "[findProp]\t",querystring
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        t.propList.append([x["prop"]["value"],x["propLabel"]["value"]])
    if len(t.propList) == 0:
        propCounter += 1
        print "[findProp]\t","has no properties. Retrying with another Instance (Attempt: " + str(propCounter) + "/10)"
        if propCounter < 10:
            findInst(t)
        else:
            possibleResult = [str(t.instance[1]) + " is " + voorzetsel + " " + str(t.concept[1]) + ".","Do you know the "+ str(t.concept[1]) + " " + str(t.instance[1]) + "?"]
            rand = int(random.randrange(len(possibleResult)))
            t.finalResult = possibleResult[rand]
            propCounter = 0
            exit
    else:
        print "[findProp]\t","Has",len(t.propList),"properties."
        rand = int(random.randrange(len(t.propList)))
        t.property = t.propList[rand]
        print "[findProp]\t",t.property
        findVal(t)

def findVal(t):
    print ""
    global voorzetsel
    t.valueList = []
    # Query for value of found property!
    querystring='''SELECT DISTINCT ?valueLabel WHERE { <''' + str(t.instance[0]) + '''> <'''  + str(t.property[0]) + '''> ?valueLabel . FILTER( (langMatches(lang(?valueLabel),'en'))||(!langMatches(lang(?valueLabel),"*")) ) }'''
    # print "[findVal]\t",querystring
    sparql.setQuery(querystring)
    results = sparql.query().convert()
    for x in results["results"]["bindings"]:
        t.valueList.append(x["valueLabel"]["value"])

    # Results
    print "[findVal]\t","Property:",t.property[1],"(has",len(t.valueList),"values)"
    
    # If there are values:  
    if len(t.valueList) > 0:
        # pick a value
        rand = int(random.randrange(len(t.valueList)))
        t.value = t.valueList[rand]
        
        # query for domain
        querystring='''SELECT DISTINCT ?domLabel WHERE { <''' + str(t.instance[0]) + '''> ?p ?valueLabel . ?p rdfs:domain ?dom . ?dom rdfs:label ?domLabel . FILTER( (langMatches(lang(?domLabel),'en'))||(!langMatches(lang(?domLabel),"*")) )}'''
        sparql.setQuery(querystring)
        results = sparql.query().convert()
        t.domain = []
        for x in results["results"]["bindings"]:
            t.domain.append(x["domLabel"]["value"])

        # print val + domain
        print "[findVal]\t","Value:",t.value
        print "[findVal]\t","Domain:",t.domain

        if t.value in t.instance:
            findProp(t)

        if "person" in t.domain:
            print "[findVal]\t",t.domain
            print "[findVal]\t","We're talking about a human!"
            line1 = str(t.instance[1]) + " is " + voorzetsel + " " + str(t.concept[1]) + ". " + "His/her " + str(t.property[1]) + " is " + str(t.value) + "."
            line2 = "Do you know the "+ str(t.concept[1]) + " " + str(t.instance[1]) + "? His/her "  + str(t.property[1]) + " is " + str(t.value) + "."
        else:
            print "[findVal]\t","We're talking about a thing..."
            line1 = str(t.instance[1]) + " is " + voorzetsel + " " + str(t.concept[1]) + ". " + "Its " + str(t.property[1]) + " is " + str(t.value) + "."
            line2 = "Do you know the "+ str(t.concept[1]) + " " + str(t.instance[1]) + "? Its "  + str(t.property[1]) + " is " + str(t.value) + "."

        line3 = voorzetsel + " " + str(t.concept[1]) + " with " + str(t.property[1]) + " " + str(t.value) + "? " + str(t.instance[1]) + "!"
        line4 = "Did you know the " + str(t.property[1]) + " of " + str(t.concept[1]) + " " + str(t.instance[1]) + " is " + str(t.value) + "?"
        possibleResult = [line1,line2,line3,line4]
        rand = int(random.randrange(len(possibleResult)))
        t.finalResult = possibleResult[rand]

    # If there are no values:
    else:
        # Try next property of propList
        print "[findVal]\t","Trying another property."
        t.propList.remove(t.property)
        print "[findVal]\t",len(t.propList),"properties left to try."
        rand = int(random.randrange(len(t.propList)))
        t.property = t.propList[rand]
        print "[findVal]\t",t.property
        findVal(t)
		
getConcepts()
sched = Scheduler()
sched.start()
    # Re-boot Twitter twice a day
sched.add_cron_job(startTwitter,hour=12)
    # Check Mentions once a minute
sched.add_cron_job(checkMentions,second=40)
    # Post a random tweet every 60 min
sched.add_cron_job(randomTweet, minute=59)
signal.pause()
