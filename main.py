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
0xD7191C; 0xFDAE61; 0xFFFFBF; 0xA6D96A; 0x1A9641;
# Make a static Google Map
GMAPS_URL = 'http://maps.googleapis.com/maps/api/staticmap?zoom=12&size=400x150&sensor=false&'
MARKER_COLORS = {None:'0xBABABA', 5:'0xD7191C', 4:'0xFDAE61', 3:'0xFFFFBF', 2:'0xA6D96A', 1:'0x1A9641'} 
def gmaps_img(points):
    markers = '&'.join('markers=%s,%s' % (p['latitude'], p['longitude']) for p in points)
    logging.info(GMAPS_URL+markers)
    return GMAPS_URL + markers


# Query Factual API for a specific string, filtered by ZIP code
# TODO: default to user's ZIP if none specified
def factual_zip_query(zipcode, search_str="Starbucks"):
    rests = factual.table('places').search(search_str)
    query = rests.filters({'postcode': zipcode})
    logging.info(query.data())
    return query.data()

def factual_get_zip_id(zipcode):
    logging.info(zipcode)
    params = 'select=factual_id,name,placetype&filters={"$and":[{"name":{"$eq":"%s"}},{"country":{"$eq":"us"}},{"placetype":{"$eq":"postcode"}}]}' % str(zipcode)
    return json.loads(factual.raw_read('t/world-geographies', str(params)))['response']['data'][0]['factual_id']
    
def factual_latlong_from_id(zipcode):
    logging.info(zipcode)
    zip_id = factual_get_zip_id(zipcode)
    params = 'select=name,country,latitude,longitude,placetype,neighbors,ancestors&filters={"factual_id":{"$eq":"%s"}}' % zip_id
    response = json.loads(factual.raw_read('t/world-geographies', str(params)))
    if response:
        params = {}
        for p in ['latitude', 'longitude']:
            params[p] = response['response']['data'][0][p]
        return [params]

def get_restaurants_in_radius(lat, lon):
    query = factual.table('places').select('name').filters({'category':{'$bw':'Food & Beverage > Restaurants'}})
    query = query.geo({"$circle":{"$center":[lat, lon], "$meters":5000}})
    return query.data()

def factual_restaurants_in_zip(zipcode):
    #TODO: Only grabbing default number of results. Need to get a total row count and page through the results to get everything
    result = factual.table('restaurants-us').select('name,category,rating,attire,price,latitude,longitude').filters({'$and':[{'postcode':zipcode},{'country':'US'},{'category':{'$bw':'Food & Beverage > Restaurants'}}]}).data()
    tally = {zipcode:{}}
    for i in ['name','category','rating','attire','price']:
        tally[zipcode][i] = factual_tally(factual_attr=i, result=result)
    tally['rated_coords'] = []
    for r in result:
        if r.get('latitude') and r.get('longitude'):
            tally['rated_coords'].append({'price':r.get('price'), 'latitude':r.get('latitude'), 'longitude':r.get('longitude')})
    return tally

def factual_zip_dining_summary(zipcode):
    COMMON_FILTERS = {'$and':
                      [{'postcode':str(zipcode)},
                       {'country':'US'},
                       {'category':
                        {'$bw':'Food & Beverage > Restaurants'}},
                       {'placeholder':''}
                       ]
                      }
    SPECIAL_FILTERS = [{'under $15':{'price':'1'}},
                       {'over $50':{'price':{"$gte":4}}},
                       {"McDonald's":{'name':"McDonald's"}},
                       {"sushi":{'cuisine':{"$search":"Sushi"}}},
                       {"steak":{'cuisine':{"$search":"Steak"}}}]
    zip_summary = {}
    for f in SPECIAL_FILTERS:
        COMMON_FILTERS['$and'][-1] = f.values()[0] 
        query = factual.table('restaurants-us').filters(COMMON_FILTERS).include_count(True)
        zip_summary[f.keys()[0]] = query.total_row_count()
    zip_summary['Starbucks'] = factual.table('places').filters({"$and":[{'postcode':str(zipcode)},{"country":"US"},{"name":{"$search":"starbucks"}}]}).include_count(True).total_row_count() 
    return zip_summary

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
        params = {'recipient_ft':kwargs['candidate'], 'cycle':'2012', 'date':'><|2011-06-30|2012-06-30', 'per_page':'50000'}
        if kwargs.get('state'):
            params['contributor_state'] = kwargs['state']
        contributions = pol_contributions(**params)
        kwargs['zip_by_amount'], kwargs['zip_by_number'] = top_zips(contributions)
        kwargs['rest_data_amt'] = factual_zip_dining_summary(kwargs['zip_by_amount'][0])
        kwargs['rest_data_num'] = factual_zip_dining_summary(kwargs['zip_by_number'][0])
        kwargs['img_url_amt'] = gmaps_img(factual_latlong_from_id(kwargs['zip_by_amount'][0]))
        kwargs['img_url_num'] = gmaps_img(factual_latlong_from_id(kwargs['zip_by_number'][0]))
        self.render('main.html', **kwargs)



app = webapp2.WSGIApplication([('/', MainPage)], debug=True)

