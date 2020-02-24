from datetime import datetime
import os

from .selenium import MapsSelenium


def run(*args, **kwargs):
    now = datetime.now()
    filename = now.strftime('%Y-%M-%d-%H-%M-%S.csv')
    search = input('Enter your maps search: ')
    file = open(os.path.join(os.getcwd(), filename), 'w+')
    MapsSelenium(file=file, search=search)
    file.close()
