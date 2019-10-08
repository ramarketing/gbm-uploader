from time import sleep
from threading import Thread

from .selenium import FlowSelenium
from .service import AccountService, CodeService, GMBService, LeadService
from ..config import STATUS_PROCESSING


def run(*args, **kwargs):
    account_service = AccountService()
    code_service = CodeService()
    gmb_service = GMBService()
    lead_service = LeadService()

    code = code_service.get_list(limit=1, has_code=3, status='null')

    while code.count == 0:
        print('No codes. Waiting 5 seconds...')
        sleep(5)
        code = code_service.get_list(limit=1, has_code=3, status='null')

    code = code[0]
    gmb_list = gmb_service.get_list(limit=5)
    lead = lead_service.get_detail(pk=code.person['id'])
    lead.patch(status=STATUS_PROCESSING)

    for gmb in gmb_list:
        if not gmb.account:
            continue

        def run_window():
            account = account_service.get_detail(gmb.account)
            FlowSelenium(gmb, account, code, lead)

        Thread(target=run_window).start()
