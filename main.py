import webapp2
import jinja2
import logging
import sys
import os
import json
import urllib2
import re
from collections import Counter
from factual.api import Factual
factual = Factual(key='pkH5QydKEI2VJhHyKgiwP9Lrb7mn5HAC0rJdlzAC', secret='nnJ7VxEvZH9TPtsbZlJWukbtgXiD57c6vcqVBsTF')


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

# Make a static Google Map
GMAPS_URL = 'http://maps.googleapis.com/maps/api/staticmap?size=400x150&sensor=false&'
def gmaps_img(points):
    markers = '&'.join('markers=%s,%s' % (p['latitude'], p['longitude']) for p in points)
    return GMAPS_URL + markers


# Query Factual API for a specific string, filtered by ZIP code
# TODO: default to user's ZIP if none specified
def factual_zip_query(zipcode, search_str="Starbucks"):
    rests = factual.table('places').search(search_str)
    query = rests.filters({'postcode': zipcode})
    logging.info(query.data())
    return query.data()

def factual_get_zip_id(zipcode):
    return json.loads(factual.raw_read('t/world-geographies', 'select=factual_id,name,placetype&filters={"$and":[{"name":{"$eq":%s}},{"country":{"$eq":"us"}},{"placetype":{"$eq":"postcode"}}]}' % zipcode))['response']['data'][0]['factual_id']
    
def factual_info_from_id(factual_id):
    response = json.loads(factual.raw_read('t/world-geographies', 'select=name,country,latitude,longitude,placetype,neighbors,ancestors&filters={"factual_id":{"$eq":"%s"}}' % factual_id))
    if response:
        params = {}
        for p in ['name', 'placetype', 'latitude', 'longitude']:
            params[p] = response['response']['data'][0][p]
        return params

def get_restaurants_in_radius(lat, lon):
    query = factual.table('places').select('name').filters({'category':{'$bw':'Food & Beverage > Restaurants'}})
    query = query.geo({"$circle":{"$center":[lat, lon], "$meters":5000}})
    return query.data()

def factual_restaurants_in_zip(zipcode):
    result = factual.table('restaurants-us').select('name,category,rating,attire,price').filters({'$and':[{'postcode':zipcode},{'category':{'$bw':'Food & Beverage > Restaurants'}}]}).data()
    tally = {zipcode:{}}
    for i in ['name','category','rating','attire','price']:
        tally[zipcode][i] = factual_tally(factual_attr=i, result=result)
    return tally

def factual_tally(factual_attr='price', result=''):
    c = Counter([i.get(factual_attr) for i in result])
    c_sort = sorted(c.items(), key=lambda x: x[0])
    if factual_attr == 'category':
        for i in range(len(c_sort)):
            c_sort[i] = (str(category_clean(c_sort[i][0])), c_sort[i][1])
    return c_sort

    
# Sunlight Campaign finance calls
APIKEY = '81ae602f16f34cbc9fe2643c7691f3d3'

def pol_search(text):
    ENTITY_SEARCH_URL = 'http://transparencydata.com/api/1.0/entities.json?apikey=%s&search=' % APIKEY
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
    zip_by_amount = sorted(zips.iteritems(), key=lambda x: x[1][1])
    zip_by_number = sorted(zips.iteritems(), key=lambda x: x[1][0])
    logging.info(zip_by_amount[-1])
    return zip_by_amount[-1], zip_by_number[-1] 

def category_clean(cat_string):
    return re.findall('[\w ]+$', cat_string)[0].lstrip()

### MAIN CLASSES

class MainPage(Handler):    
    def get(self):
        self.render('main.html')

    def post(self):
        kwargs = {}
        kwargs['candidate'] = self.request.get('candidate')
        kwargs['state'] = self.request.get('state')
        params = {'recipient_ft':kwargs['candidate'], 'cycle':'2012', 'date':'><|2011-10-01|2012-06-30', 'per_page':'50000'}
        if kwargs.get('state'):
            params['contributor_state'] = kwargs['state']
        contributions = pol_contributions(**params)
        kwargs['zip_by_amount'], kwargs['zip_by_number'] = top_zips(contributions)
        kwargs['rest_data_amt'] = factual_restaurants_in_zip(kwargs['zip_by_amount'][0])
        kwargs['rest_data_num'] = factual_restaurants_in_zip(kwargs['zip_by_number'][0])
        kwargs['img_url_amt'] = gmaps_img(factual_zip_query(kwargs['zip_by_amount'][0]))
        kwargs['img_url_num'] = gmaps_img(factual_zip_query(kwargs['zip_by_number'][0]))
        self.render('main.html', **kwargs)



app = webapp2.WSGIApplication([('/', MainPage)], debug=True)

