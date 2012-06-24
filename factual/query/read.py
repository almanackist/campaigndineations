from base import Base

class Read(Base):
    def __init__(self, api, path, params):
        self.response = None
        Base.__init__(self, api, path, params)

    def data(self):
        return self.get_response()['data']

    def total_row_count(self):
        return self.get_response()['total_row_count']

    def included_rows(self):
        return self.get_response()['included_rows']


    def get_response(self):
        if not self.response:
            self.response = self.api.get(self)
        return self.response
