from read import Read

class Resolve(Read):
    def __init__(self, api, values={}):
        Read.__init__(self, api, 'places/resolve', values)

    def values(self, values):
        return self._copy({'values': values})

    def include_count(self, include):
        return self._copy({'include_count': include})

    def _copy(self, params):
        return Resolve(self.api, self.merge_params(params))
