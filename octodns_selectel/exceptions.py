from octodns.provider import ProviderException

class SelectelException(ProviderException):
   def __init__(self, message):
        super().__init__(message)

class ApiException(SelectelException):
   def __init__(self, message):
        super().__init__(message)

class AuthException(ApiException):
    def __init__(self):
        message = 'Authorization failed. Invalid or empty token.'
        super().__init__(message)