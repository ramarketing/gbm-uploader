from concurrent.futures import ThreadPoolExecutor
from json.decoder import JSONDecodeError
from time import sleep
from threading import Thread

from .selenium import GMBTaskSelenium
from .service import GMBTaskService
from . import constants


def _run_object(obj):
    obj.patch(status=constants.STATUS_RUNNING)
    try:
        GMBTaskSelenium(gmbtask=obj)
    except Exception as err:
        obj.patch(
            status=constants.STATUS_FAIL, status_message=str(err)
        )


def _run_object_list(object_list):
    executor = ThreadPoolExecutor(max_workers=3)
    futures = []

    for obj in object_list:
        a = executor.submit(_run_object, obj)
        futures.append(a)


def run(*args, **kwargs):
    gmbtask_service = GMBTaskService()
    object_list = None
    next_ = True

    while True:
        while next_:
            try:
                if object_list is None:
                    object_list = gmbtask_service.get_list()
                else:
                    object_list.get_next_page()

                next_ = True if object_list.next else False
                _run_object_list(object_list)
            except JSONDecodeError:
                print('Connection error, waiting 5 seconds.')
                sleep(5)

        object_list = None
        next_ = True
        sleep(10)
