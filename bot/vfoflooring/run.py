from .selenium import VFOSelenium


def run(*args, **kwargs):
    selenium = VFOSelenium()
    selenium()
