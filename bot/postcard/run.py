from .selenium import PostcardSelenium
from .service import PostcardService


def run(*args, **kwargs):
    postcard_service = PostcardService()
    object_list = postcard_service.get_list()

    for obj in object_list:
        PostcardSelenium(postcard=obj)
