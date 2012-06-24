"""
Base query class
"""

class Base(object):
    def __init__(self, api, path, params):
        self.api = api
        self.path = path
        self.params = params

    def get_url(self):
        return self.api.build_url(self.path, self.params)

    def merge_params(self, params):
        new_params = self.params.copy()
        new_params.update(params)
        return new_params
