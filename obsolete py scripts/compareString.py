from difflib import SequenceMatcher

def compareString(s1,s2):
    s = SequenceMatcher(None,s1,s2)
    print str(float(s.ratio())*100) + str("% similar")
    
