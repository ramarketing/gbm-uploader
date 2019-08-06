import os
import requests

from . import config


def phone_clean(value):
    value = value \
        .replace('-', '') \
        .replace('(', '') \
        .replace(')', '') \
        .replace(' ', '')
    return value


def save_image_from_url(url, name):
    if '.' not in name:
        name = '{}.{}'.format(name, url.split('.')[-1])

    path = os.path.join(config.BASE_DIR, 'img', name)
    response = requests.get(url)
    file = open(path, "wb")
    file.write(response.content)
    file.close()
    return path
