class GBMException(Exception):
    def __init__(self, msg=None, logger=None):
        if logger:
            self.logger(instance=self, data=msg)
        return super().__init__(msg)


class CaptchaError(GBMException):
    pass


class EntityBypass(GBMException):
    pass


class EntityInvalid(GBMException):
    pass


class EmptyList(GBMException):
    pass


class NotFound(GBMException):
    pass
