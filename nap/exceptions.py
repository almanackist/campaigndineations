class NapBaseException(Exception):
    """
    All Nap exceptions inherit from this exception.
    """


class NapHttpBaseException(NapBaseException):
    """
    All Nap HTTP Exceptions inherit from this exception.

    Instances of this class have these attributes to expose information
    about the HTTP request that raised this exception to the calling code:

    'response' is an instance of 'httplib2.Response' as returned
    by 'httplib2.Http.request()'.

    'content' is a string that contains the response entity body.
    """

    def __init__(self, desc, response, content):
        """
        Constructor.

        'desc' is a string containing an error message, usually taken 
        from a caught upstream exception.

        'response' is an instance of 'httplib2.Response' as returned
        by 'httplib2.Http.request()'.

        'content' is a string that contains the response entity body.
        """
        # I'm doing things the way httplib2.HttpLib2ErrorWithResponse
        # does things.
        self.response = response
        self.content = content
        super(NapHttpBaseException, self).__init__(desc)


class HttpClientError(NapHttpBaseException):
    """
    Called when the server tells us there was a client error (4xx).
    """


class HttpServerError(NapHttpBaseException):
    """
    Called when the server tells us there was a server error (5xx).
    """


class SerializerNoAvailable(NapBaseException):
    """
    There are no available Serializers.
    """


class SerializerNotAvailable(NapBaseException):
    """
    The chosen Serializer is not available.
    """

class SerializerError(NapBaseException):
    """
    All serialization/deserializations inherit from this class. 
    """
    pass

class SerializerEncodeError(SerializerError):
    """
    There was a problem serializing data.

    The 'desc' is a string containing the error message, usually
    obtained from catching an upstream exception.

    The 'content' is a string thjat contains the response entity body
    as returned by 'httplib2.Http.request()'.
    """
    def __init__(self, desc, content):
        self.content = content
        super(SerializerEncodeError, self).__init__(desc)

class SerializerDecodeError(SerializerError):
    """
    There was a problem deserializing data.
    """
    pass

class ImproperlyConfigured(NapBaseException):
    """
    Nap is somehow improperly configured.
    """
