from .selenium import RenamerSelenium
from .service import BusinessService


def run(*args, **kwargs):
    biz_service = BusinessService()
    object_list = biz_service.get_list()

    for obj in object_list:
        RenamerSelenium(entity=obj)
