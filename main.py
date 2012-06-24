import webapp2
import jinja2
import logging
import sys
import os
import json
from factual.api import Factual
factual = Factual(key='pkH5QydKEI2VJhHyKgiwP9Lrb7mn5HAC0rJdlzAC', secret='nnJ7VxEvZH9TPtsbZlJWukbtgXiD57c6vcqVBsTF')

#sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dev.env/lib/python2.7/site-packages/'))



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


class MainPage(Handler):
    
    def get(self):
        self.render('main.html')

    def post(self):
        zipcode = self.request.get('zip')
        img_url = gmaps_img(factual_query(zipcode))
        self.render('main.html', img_url=img_url)



app = webapp2.WSGIApplication([('/', MainPage)], debug=True)

