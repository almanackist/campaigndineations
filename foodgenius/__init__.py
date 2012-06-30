import nap
import oauth2

API_DOMAIN = 'getfoodgenius.com'
API_VERSION = '0.1'

class FoodGeniusResource(nap.Resource):

    class Meta:
        http = oauth2.Client

    def _get_client(self):
        consumer = oauth2.Consumer(self._meta.authentication.get('key'),
            self._meta.authentication.get('secret'))

        return self._meta.http(consumer)

    def request(self, method, **kwargs):
        if "body" not in kwargs:
            # httplib2's request method sets the default body to None, but
            # oauth2's method sets the default to an empty string. We need
            # to play nice with oauth2
            kwargs["body"] = ""

        return super(FoodGeniusResource, self).request(method, **kwargs)

def Foodgenius(authentication, domain=API_DOMAIN, version=API_VERSION):
    return nap.Api(domain=domain,
        resource_class=FoodGeniusResource,
        authentication=authentication,
        uri="/api/%s/" % API_VERSION)
