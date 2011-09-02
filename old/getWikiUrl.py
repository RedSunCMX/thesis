import urllib
import urllib2
from BeautifulSoup import BeautifulSoup
import nltk
from pprint import pprint

title= "Apoptosis"
article = urllib.quote(title)

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')] #wikipedia needs this

resource = opener.open("http://en.wikipedia.org/wiki/" + article)
data = resource.read()
resource.close()
soup = BeautifulSoup(data)
text = str(soup.findAll('p'))
clean = nltk.clean_html(text)
print clean
