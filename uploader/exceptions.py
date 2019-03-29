from logger import UploaderLogger


logger = UploaderLogger()


class CredentialBypass(Exception):
    def __init__(self, msg=None):
        logger(instance=self, data=msg)
        return super().__init__(msg)


class CredentialInvalid(Exception):
    def __init__(self, msg=None):
        logger(instance=self, data=msg)
        return super().__init__(msg)


class CredentialPendingVerification(Exception):
    def __init__(self, msg=None):
        logger(instance=self, data=msg)
        return super().__init__(msg)


class EmptyUpload(Exception):
    def __init__(self, msg=None):
        logger(instance=self, data=msg)
        return super().__init__(msg)
