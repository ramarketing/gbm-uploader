class GBMException(Exception):
    def __init__(self, msg=None, logger=None):
        if logger:
            logger(instance=self, data=msg)
        return super().__init__(msg)


class CaptchaError(GBMException):
    pass


class CredentialInvalid(GBMException):
    pass


class EntityBypass(GBMException):
    pass


class EntityInvalid(GBMException):
    pass


class EntityIsSuccess(GBMException):
    pass


class EmptyList(GBMException):
    pass


class InvalidValidationMethod(GBMException):
    pass


class NotFound(GBMException):
    pass


class MaxRetries(GBMException):
    pass


class TerminatedByUser(GBMException):
    pass
