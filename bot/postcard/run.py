from json.decoder import JSONDecodeError
from time import sleep

from selenium.common.exceptions import ElementClickInterceptedException

from .selenium import PostcardSelenium
from .service import PostcardService
from ..base .exceptions import CredentialInvalid, MaxRetries


def _run(object_list):
    for obj in object_list:
        if not obj.verification_address and not obj.name:
            continue
        obj.patch(status='creating')
        try:
            PostcardSelenium(postcard=obj)
            if obj.recipient:
                obj.patch(status='requested')
            else:
                obj.patch(status='created')
        except (MaxRetries, ElementClickInterceptedException):
            obj.patch(status='not-created')
        except CredentialInvalid:
            obj.patch(status='denied')


def run(*args, **kwargs):
    postcard_service = PostcardService()
    object_list = None
    next_ = True

    while True:
        while next_:
            try:
                if object_list is None:
                    object_list = postcard_service.get_list()
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
