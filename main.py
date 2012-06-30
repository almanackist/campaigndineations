import webapp2
import jinja2
import logging
import os
import json
import urllib
import urllib2
import re
import time
from foodgenius import Foodgenius
from google.appengine.api import memcache
from collections import Counter
from factual.api import Factual
factual = Factual(key='pkH5QydKEI2VJhHyKgiwP9Lrb7mn5HAC0rJdlzAC', secret='nnJ7VxEvZH9TPtsbZlJWukbtgXiD57c6vcqVBsTF')
fg = Foodgenius(authentication={'key': 'sHLw25GEjbvCfWrCBA', 'secret': 'kB2ZdGuzVQm3AfafgjBLqE6RLQNVfqwT'})

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
GMAPS_URL = 'http://maps.googleapis.com/maps/api/staticmap?zoom=11&size=320x150&sensor=false&'
MARKER_COLORS = {None:'0xBABABA', 5:'0xD7191C', 4:'0xFDAE61', 3:'0xFFFFBF', 2:'0xA6D96A', 1:'0x1A9641'} 
def gmaps_img(points):
    markers = '&'.join('markers=%s,%s' % (p['latitude'], p['longitude']) for p in points)
    return GMAPS_URL + markers

def gmaps_img_zip(zipcode):
    return GMAPS_URL + "markers=%s" % zipcode


def foodgenius_expensive_nearby(zipcode):
    lat, lon = factual_latlong_from_id(zipcode)
    (headers, response) = fg.menus.near(lat+"@"+lon).get(order_by='-price', min_price='1.00')
    logging.info(response)
    if response['menu_items']:
        return "$%.2f for %s at %s (%s)" % (response['menu_items'][0]['price'], 
                                            response['menu_items'][0]['name'], 
                                            response['menu_items'][0]['location']['restaurant']['name'], 
                                            response['menu_items'][0]['location']['place']['street'] )

# TODO: default to user's state if none specified
def factual_zip_query(zipcode, search_str="Starbucks"):
    rests = factual.table('places').search(search_str)
    query = rests.filters({'postcode': zipcode})
    return query.data()

def factual_get_zip_id(zipcode):
    params = 'select=factual_id,name,placetype&filters={"$and":[{"name":{"$eq":"%s"}},{"country":{"$eq":"us"}},{"placetype":{"$eq":"postcode"}}]}' % str(zipcode)
    return json.loads(factual.raw_read('t/world-geographies', str(params)))['response']['data'][0]['factual_id']
    
def factual_latlong_from_id(zipcode):
    zip_id = factual_get_zip_id(zipcode)
    params = 'select=name,country,latitude,longitude,placetype,neighbors,ancestors&filters={"factual_id":{"$eq":"%s"}}' % zip_id
    response = json.loads(factual.raw_read('t/world-geographies', str(params)))
    if response:
#        params = {}
#        for p in ['latitude', 'longitude']:
#            params[p] = response['response']['data'][0][p]
        return str(response['response']['data'][0]['latitude']), str(response['response']['data'][0]['longitude']) 

def get_restaurants_in_radius(lat, lon):
    query = factual.table('places').select('name').filters({'category':{'$bw':'Food & Beverage > Restaurants'}})
    query = query.geo({"$circle":{"$center":[lat, lon], "$meters":5000}})
    return query.data()

def factual_restaurants_in_zip(zipcode):
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
                       {'placeholder':""}
                       ]
                      }
    SPECIAL_FILTERS = [{'meals < $15':{'price':'1'}},
                       {'meals > $50':{'price':{"$gte":4}}},
                       {"sushi":{'cuisine':{"$search":"Sushi"}}},
                       {"steak":{'cuisine':{"$search":"Steak"}}},
                       {"McDonald's":{'name':"McDonald's"}}]
    zip_summary = []
#    COMMON_FILTERS['$and'][-1] = {'name':"McDonald's"}
#    logging.info(COMMON_FILTERS)
#    time.sleep(0.01)
#    name_query = factual.facets('restaurants-us').select('name').filters(COMMON_FILTERS).data()
    COMMON_FILTERS['$and'].pop()
    logging.info(COMMON_FILTERS)
    time.sleep(0.01)
    price_query = factual.facets('restaurants-us').select('price').filters(COMMON_FILTERS).data()

    zip_summary.append(['restaurants by price range:', 0])
    zip_summary.append(['$75+', sum([price_query['price'][i] for i in price_query['price'] if i == '5'])])
    zip_summary.append(['$50-$75', sum([price_query['price'][i] for i in price_query['price'] if i == '4'])])
    zip_summary.append(['$30-$50', sum([price_query['price'][i] for i in price_query['price'] if i == '3'])])
    zip_summary.append(['$15-$30', sum([price_query['price'][i] for i in price_query['price'] if i == '2'])])
    zip_summary.append(['<$15', sum([price_query['price'][i] for i in price_query['price'] if i == '1'])])
#    zip_summary.append(["McDonald's", sum([name_query['name'][i] for i in name_query['name'] if i.lower() == "mcdonald's"])])                              

#    for f in SPECIAL_FILTERS:
#        COMMON_FILTERS['$and'][-1] = f.values()[0] 
#        try:
#            query = factual.table('restaurants-us').filters(COMMON_FILTERS).include_count(True)
#            zip_summary.append([f.keys()[0], query.total_row_count()])
#        except:
#            zip_summary.append([f.keys()[0], "failed on %s" % f])

#    zip_summary.append(['Starbucks', factual.table('places').filters({"$and":[{'postcode':str(zipcode)},{"country":"US"},{"name":{"$search":"starbucks"}}]}).include_count(True).total_row_count()]) 
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
    zip_by_amount.reverse()
    return zip_by_amount[:3] 
 

def category_clean(cat_string):
    return re.findall('[\w ]+$', cat_string)[0].lstrip()

### MAIN CLASSES

DEFAULT = {'tables': ['table0', 'table1', 'table2'], 'candidate': u'Barack Obama', 'top_zips': [(u'10024', [278, 259375.0]), (u'10023', [237, 211436.0]), (u'10011', [187, 179485.0])], 'img_urls': ['http://maps.googleapis.com/maps/api/staticmap?zoom=11&size=320x150&sensor=false&markers=40.78701,-73.977814', 'http://maps.googleapis.com/maps/api/staticmap?zoom=11&size=320x150&sensor=false&markers=40.775681,-73.986954', 'http://maps.googleapis.com/maps/api/staticmap?zoom=11&size=320x150&sensor=false&markers=40.741669,-74.004044'], 'rest_data': [[['restaurants by price range:', 0], ['$75+', 4], ['$50-$75', 9], ['$30-$50', 23], ['$15-$30', 66], ['<$15', 34]], [['restaurants by price range:', 0], ['$75+', 2], ['$50-$75', 16], ['$30-$50', 24], ['$15-$30', 43], ['<$15', 29]], [['restaurants by price range:', 0], ['$75+', 7], ['$50-$75', 24], ['$30-$50', 44], ['$15-$30', 104], ['<$15', 63]]], 'state': u'NY'}

class MainPage(Handler):    
    def get(self):
        self.render('main.html', **DEFAULT)

    def post(self):
        kwargs = {}
        candidate = self.request.get('candidate')
        state = self.request.get('state')
        cached_data = memcache.get(",".join([candidate,state]))
        if cached_data:
            kwargs = cached_data
        else:
            kwargs['candidate'] = self.request.get('candidate')
            kwargs['state'] = self.request.get('state')
            params = {'recipient_ft':urllib.quote_plus(kwargs['candidate']), 'contributor_state':kwargs['state'], 'cycle':'2012', 'date':'><|2011-09-01|2012-06-30', 'per_page':'50000'}
            contributions = pol_contributions(**params)
            kwargs['top_zips'] = top_zips(contributions)
            kwargs['tables'] = ['table0', 'table1', 'table2']
            kwargs['rest_data'] = [factual_zip_dining_summary(i[0]) for i in kwargs['top_zips']]

#            kwargs['img_urls'] = [gmaps_img(factual_latlong_from_id(i[0])) for i in kwargs['top_zips']]
#            data = factual.raw_read('/multi',{"queries":{"place":"/places/t/global?geo={'$point':[34.06021,-118.41828]}&limit=1","place2":{"place":"/places/t/global?geo={'$point':[35.06021,-118.41828]}&limit=1"}}})
#            logging.info(data)

            kwargs['priciest_dish'] = [foodgenius_expensive_nearby(i[0]) for i in kwargs['top_zips']]

                        
            kwargs['img_urls'] = [gmaps_img_zip(str(i[0])) for i in kwargs['top_zips']]
            logging.info(kwargs['rest_data'])
            memcache.set(",".join([candidate,state]), kwargs)
        self.render('main.html', **kwargs)

factual.raw_read('multi',{"queries":{"get-postcode":{"t/places":"filters=%7B%22postcode%22%3A%2290067%22%7D"},"get-facet":{"t/places/facets":'filters=%7B%22postcode%22%3A%2290067%22%7D&select=category'}}})
class HackPage(MainPage):
    def get(self):
        if self.request.get('candidate') and self.request.get('state'):
            return self.post()
        self.render('main.html', **DEFAULT)

    def post(self):
        kwargs = {}
        candidate = self.request.get('candidate')
        state = self.request.get('state')
        cached_data = memcache.get(",".join([candidate,state]))
        if cached_data:
            kwargs = cached_data
        else:
            kwargs['candidate'] = self.request.get('candidate')
            kwargs['state'] = self.request.get('state')
            params = {'recipient_ft':urllib.quote_plus(kwargs['candidate']), 'contributor_state':kwargs['state'], 'cycle':'2012', 'date':'><|2011-09-01|2012-06-30', 'per_page':'50000'}
            contributions = pol_contributions(**params)
            kwargs['top_zips'] = top_zips(contributions)
            kwargs['tables'] = ['table0', 'table1', 'table2']
            kwargs['rest_data'] = [factual_zip_dining_summary(i[0]) for i in kwargs['top_zips']]
#            kwargs['img_urls'] = [gmaps_img(factual_latlong_from_id(i[0])) for i in kwargs['top_zips']]
            kwargs['img_urls'] = [gmaps_img_zip(str(i[0])) for i in kwargs['top_zips']]
            memcache.set(",".join([candidate,state]), kwargs)
        self.render('hack.html', **kwargs)
    

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/hack', HackPage)], debug=True)

