from wikitools import wiki,api
from pprint import pprint
import nltk

def get(title):
	title = "'" + title + "'"
	site = wiki.Wiki('http://en.wikipedia.org/w/api.php')
	params = {'action':'query', 'prop':'revisions', 'rvprop':'content', 'format':'xml', 'titles':title }
	request = api.APIRequest(site,params)
	result = request.query()
	print result
	clean = nltk.clean_html(str(result))
	pprint(clean)
