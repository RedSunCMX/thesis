import urllib
import urllib2
from BeautifulSoup import BeautifulSoup
import nltk
from pprint import pprint

article= "Apoptosis"
article = urllib.quote(article)

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')] #wikipedia needs this

resource = opener.open("http://en.wikipedia.org/wiki/" + article)
data = resource.read()
resource.close()
soup = BeautifulSoup(data)
#pprint(soup)
clean = nltk.clean_html(str(soup))
#print clean
print soup.find('div',id="content").p
