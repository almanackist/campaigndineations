"""
Reverse geocode query
"""

from read import Read

class Geocode(Read):
    def __init__(self, api, path, point):
        Read.__init__(self, api, path, point)

    def point(point):
        return self._copy({'geo': point})

    def _copy(self, params):
        return Geocode(self.api, self.path, self._merge_params(params))
