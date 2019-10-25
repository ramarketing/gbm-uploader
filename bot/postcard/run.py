from .selenium import PostcardSelenium
from .service import PostcardService
from ..base .exceptions import MaxRetries


def run(*args, **kwargs):
    postcard_service = PostcardService()
    object_list = None
    next_ = True

    while next_:
        if object_list is None:
            object_list = postcard_service.get_list()
        else:
            object_list.get_next_page()

        next_ = True if object_list.next else False

        for obj in object_list:
            if not obj.verification_address:
                continue
            obj.patch(status='creating')
            try:
                PostcardSelenium(postcard=obj)
                obj.patch(status='requested')
            except MaxRetries:
                obj.patch(status='not-created')
