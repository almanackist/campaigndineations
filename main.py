import webapp2
import jinja2
import logging
import sys
import os
import json
import urllib2
from factual.api import Factual
factual = Factual(key='pkH5QydKEI2VJhHyKgiwP9Lrb7mn5HAC0rJdlzAC', secret='nnJ7VxEvZH9TPtsbZlJWukbtgXiD57c6vcqVBsTF')

#sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dev.env/lib/python2.7/site-packages/'))

### GLOBALS VARS
SUNLIGHT_APIKEY = '81ae602f16f34cbc9fe2643c7691f3d3'

### TEMPLATE VARIABLES
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)


### GENERAL CLASSES

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_txt)
    

### FUNCTIONS

GMAPS_URL = 'http://maps.googleapis.com/maps/api/staticmap?size=380x263&sensor=false&'
def gmaps_img(points):
    markers = '&'.join('markers=%s,%s' % (p['latitude'], p['longitude']) for p in points)
    return GMAPS_URL + markers

def factual_query(zipcode):
    rests = factual.table('places').search('starbucks')
    query = rests.filters({'postcode': zipcode})
    logging.info(query.data())
    return query.data()


APIKEY = '81ae602f16f34cbc9fe2643c7691f3d3'
ENTITY_SEARCH_URL = 'http://transparencydata.com/api/1.0/entities.json?apikey=%s&search=' % APIKEY

def pol_search(text):
    r = urllib2.urlopen(ENTITY_SEARCH_URL + text).read()
    return json.loads(r)

def pol_contributors(pol_id, limit, cycle, APIKEY):
    CONTRIB_URL = 'http://transparencydata.com/api/1.0/aggregates/pol/%s/contributors.json?apikey=%s&limit=%s&cycle=%s' % (pol_id, APIKEY, limit, cycle)
    r = urllib2.urlopen(CONTRIB_URL).read()
    return json.loads(r)

def org_recipients(org_id, APIKEY):
    ORG_RECIPIENTS_URL = 'http://transparencydata.com/api/1.0/aggregates/org/%s/recipients.json?apikey=%s&limit=5&cycle=2012' % (org_id, APIKEY)
    r = urllib2.urlopen(ORG_RECIPIENTS_URL).read()
    return json.loads(r) 

def pol_contributions(**kwargs):
    POL_CONTRIBUTIONS_URL = 'http://transparencydata.com/api/1.0/contributions.json?apikey=%s&' % APIKEY
    params = '&'.join('%s=%s' % (k,v) for (k,v) in kwargs.iteritems())
    return json.loads(urllib2.urlopen(POL_CONTRIBUTIONS_URL + params).read())

def top_zips(contributions):
    zips = {}
    for i in contributions:
        if i['contributor_zipcode'] not in zips:
            zips[i['contributor_zipcode']] = [1, float(i['amount'])]
        else:
            zips[i['contributor_zipcode']][0] += 1
            zips[i['contributor_zipcode']][1] += float(i['amount'])
    ziplist = sorted(zips.iteritems(), key=lambda x: x[1][1])
    ziplist.reverse()
    return ziplist[:10]


class MainPage(Handler):
    
    def get(self):
        self.render('main.html')

    def post(self):
        candidate = self.request.get('candidate')
        state = self.request.get('state')
        params = {'recipient_ft':candidate, 'cycle':'2012', 'contributor_state':state, 'per_page':'50000'}
        contributions = pol_contributions(**params)
        topzips = top_zips(contributions)
        topzip = topzips[0][0]
        logging.info(topzips)
        img_url = gmaps_img(factual_query(topzip))
        self.render('main.html', candidate=candidate, state=state, img_url=img_url)



app = webapp2.WSGIApplication([('/', MainPage)], debug=True)

