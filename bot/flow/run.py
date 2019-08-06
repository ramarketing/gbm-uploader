from .selenium import FlowSelenium
from .service import BusinessService, CredentialService


def run(*args, **kwargs):
    biz_service = BusinessService()
    credential_service = CredentialService()
    credential_list = credential_service.get_list()
    for credential in credential_list:
        object_list = biz_service.get_list(limit=1)

        for obj in object_list:
            FlowSelenium(entity=obj, credential=credential)
