from json.decoder import JSONDecodeError
from time import sleep

from .selenium import GMBTaskSelenium
from .service import GMBTaskService
from . import constants


def _run(object_list):
    for obj in object_list:
        obj.patch(status=constants.STATUS_RUNNING)
        try:
            GMBTaskSelenium(gmbtask=obj)
        except Exception as err:
            obj.patch(
                status=constants.STATUS_FAIL, status_message=str(err)
            )


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
                _run(object_list)
            except JSONDecodeError:
                print('Connection error, waiting 5 seconds.')
                sleep(5)

        object_list = None
        next_ = True
        sleep(10)
