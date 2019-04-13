import os
import requests

from config import BASE_DIR


def save_image_from_url(url, name):
    if '.' not in name:
        name = '{}.{}'.format(name, url.split('.')[-1])

    path = os.path.join(BASE_DIR, 'img', name)
    response = requests.get(url)
    file = open(path, "wb")
    file.write(response.content)
    file.close()
    return path
