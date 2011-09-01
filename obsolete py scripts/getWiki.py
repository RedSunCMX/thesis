from wikitools import wiki,api
from pprint import pprint
import nltk

site = wiki.Wiki('http://en.wikipedia.org/w/api.php')
params = {'action':'query', 'prop':'revisions', 'rvprop':'content', 'format':'xml', 'titles':'Apoptosis' }
request = api.APIRequest(site,params)
result = request.query()
clean = nltk.clean_html(str(result))
pprint(clean)
