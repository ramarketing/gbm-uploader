from .selenium import UploaderSelenium
from .service import CredentialService


def run(*args, **kwargs):
    credential_service = CredentialService()
    object_list = credential_service.get_list()

    for obj in object_list:
        UploaderSelenium(entity=obj)
