"""
Geopulse query
"""

from read import Read

class Geopulse(Read):
    def __init__(self, api, path, point):
        Read.__init__(self, api, path, point)

    def point(self, point):
        return self._copy({'geo': point})

    def select(self, fields):
        return self._copy({'select': fields})

    def _copy(self, params):
        return Geopulse(self.api, self.path, self.merge_params(params))
