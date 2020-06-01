from .selenium import PorchSelenium


def run(*args, **kwargs):
    selenium = PorchSelenium()
    selenium()
