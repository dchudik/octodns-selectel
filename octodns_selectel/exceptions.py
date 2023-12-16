from octodns.provider import ProviderException


class SelectelException(ProviderException):
    pass


class ApiException(SelectelException):
    pass


class AuthException(ApiException):
    pass
