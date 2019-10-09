from time import sleep
from threading import Thread

from .selenium import FlowSelenium
from .service import AccountService, CodeService, GMBService, LeadService
from ..config import STATUS_PROCESSING


def run_thread_list(*args, **kwargs):
    account_service = AccountService()
    code_service = CodeService()
    gmb_service = GMBService()
    lead_service = LeadService()
    code_kwargs = {
        'limit': 1,
        'has_code': 3,
        'status': 'null'
    }

    code = code_service.get_list(**code_kwargs)

    while code.count == 0:
        print('No codes. Waiting 5 seconds...')
        sleep(5)
        code = code_service.get_list(**code_kwargs)

    code = code[0]
    lead = lead_service.get_detail(pk=code.person['id'])
    gmb_list = gmb_service.get_list(is_created=3, limit=5)

    if gmb_list.count == 0:
        print('There are no business available. Waiting 10 seconds.')
        sleep(10)
        return

    lead.patch(status=STATUS_PROCESSING)
    code.subscribe()
    thread_list = []

    for gmb in gmb_list:
        if not gmb.account or gmb.is_created:
            continue

        def run_window():
            account = account_service.get_detail(gmb.account)
            FlowSelenium(gmb, account, code, lead)
            gmb.patch(is_created=True)

        thread = Thread(target=run_window)
        thread.start()
        thread_list.append(thread)

    return thread_list


def run(*args, **kwargs):
    thread_list = []

    while True:
        if any([thread.is_active() for thread in thread_list if thread and hasattr(thread, 'is_active')]):
            print(
                'Another thread is running in the background. '
                'Waiting 10 seconds.'
            )
            for i in range(0, 10):
                print('{}/10'.format(i + 1))
                sleep(1)
        else:
            thread_list = run_thread_list(*args, **kwargs)
