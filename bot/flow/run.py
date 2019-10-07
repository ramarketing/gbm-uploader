from .selenium import FlowSelenium
from .service import AccountService, GMBService


def run(*args, **kwargs):
    gmb_service = GMBService()
    account_service = AccountService()
    account_list = account_service.get_list()
    for account in account_list:
        gmb_list = gmb_service.get_list(limit=3)

        for gmb in gmb_list:
            FlowSelenium(gmb, account)
