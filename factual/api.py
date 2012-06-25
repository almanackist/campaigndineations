"""
Factual API driver
"""

import json
from urllib import urlencode

import requests
from oauth_hook import OAuthHook

from query import Crosswalk, Resolve, Table, Submit, Facets, Flag, Geopulse, Geocode

API_V3_HOST = "http://api.v3.factual.com"
DRIVER_VERSION_TAG = "factual-python-driver-1.2.0"

class Factual(object):
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
        self.api = API(self._generate_token(key, secret))

    def table(self, table):
        return Table(self.api, 't/' + table)

    def crosswalk(self):
        return Crosswalk(self.api)

    def resolve(self, values):
        return Resolve(self.api, {'values': values})

    def raw_read(self, path, raw_params):
        return self.api.raw_read(path, raw_params)

    def facets(self, table):
        return Facets(self.api, 't/' + table + '/facets')

    def submit(self, table, factual_id=None, values={}):
        return Submit(self.api, table, factual_id, {'values': values})

    def flag(self, table, factual_id):
        return Flag(self.api, table, factual_id)

    def geopulse(self, point={}):
        return Geopulse(self.api, 'places/geopulse', {'geo': point})

    def geocode(self, point):
        return Geocode(self.api, 'places/geocode', {'geo': point})

    def monetize(self):
        return Table(self.api, 'places/monetize')

    def _generate_token(self, key, secret):
        access_token = OAuthHook(consumer_key=key, consumer_secret=secret, header_auth=True)
        return access_token


class API(object):
    def __init__(self, access_token):
        self.client = requests.session(hooks={'pre_request': access_token})

    def get(self, query):
        response = self._handle_request(query.path, query.params)
        return response

    def post(self, query):
        response = self._make_post_request(query.path, query.params)
        return response
        
    def schema(self, query):
        response = self._handle_request(query.path + '/schema', query.params)
        return response['view']

    def raw_read(self, path, raw_params):
        url = self._build_base_url(path)
        if isinstance(raw_params, str):
            url += raw_params
        else:
            url += self._make_query_string(raw_params)
        return self._make_request(url).text

    def build_url(self, path, params):
        url = self._build_base_url(path) + self._make_query_string(params)
        return url

    def _build_base_url(self, path):
        return API_V3_HOST + '/' + path + '?'

    def _handle_request(self, path, params):
        url = self.build_url(path, params)
        response = self._make_request(url)
        payload = json.loads(response.text)
        if payload['status'] != 'ok':
            raise APIException(response.status_code, payload, url)
        return payload['response']

    def _make_request(self, url):
        headers = {'X-Factual-Lib': DRIVER_VERSION_TAG}
        response = self.client.get(url, headers=headers)
        return response

    def _make_post_request(self, path, params):
        url = self.build_url(path, params)
        headers = {'X-Factual-Lib': DRIVER_VERSION_TAG}
        response = self.client.post(url, headers=headers)
        payload = json.loads(response.text)
        if payload['status'] != 'ok':
            raise APIException(response.status_code, payload, url)
        return payload['response'] if 'response' in payload else payload

    def _make_query_string(self, params):
        string_params = []
        for key, val in params.items():
            transformed = json.dumps(val) if not isinstance(val, str) else val
            string_params.append((key, transformed))
        return urlencode(string_params)

class APIException(Exception):
    def __init__(self, status_code, response, url):
        self.status_code = status_code
        self.response = response
        self.url = url
        exception = {'http_status_code':status_code,'response':response, 'url':url}
        Exception.__init__(self, exception)

    def get_status_code(self):
        return self.status_code

    def get_response(self):
        return self.response
