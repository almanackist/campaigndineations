import webapp2
import logging
#import sys
#import os

#sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dev.env/lib/python2.7/site-packages/'))

from factual.api import Factual

factual = Factual('pkH5QydKEI2VJhHyKgiwP9Lrb7mn5HAC0rJdlzAC', 'nnJ7VxEvZH9TPtsbZlJWukbtgXiD57c6vcqVBsTF')
rests = factual.table('restaurants-us')
query = rests.filters({'locality': 'Champaign'})
logging.info(query)

class MainPage(webapp2.RequestHandler):
    
    
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Hello, webapp World!')


app = webapp2.WSGIApplication([('/', MainPage)], debug=True)

