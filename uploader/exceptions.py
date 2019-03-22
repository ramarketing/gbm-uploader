from logger import UploaderLogger


logger = UploaderLogger()


class CredentialInvalid(Exception):
    def __init__(self, msg=None):
        logger(instance=self, data=msg)
        return super().__init__(msg)


class EmptyUpload(Exception):
    def __init__(self, msg=None):
        logger(instance=self, data=msg)
        return super().__init__(msg)
