import os
import random
import re

import homoglyphs as hg
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


def permute_characters(text, replaces=2):
    chars = list(set([c for c in text.replace(' ', '')]))
    for i in range(0, replaces):
        old_char = random.choice(chars)
        if isinstance(old_char, tuple):
            continue
        new_char = random.choice(
            hg.Homoglyphs().get_combinations(old_char)
        )
        chars.pop(chars.index(old_char))
        chars.append((old_char, new_char))
    chars_map = []
    for c in chars:
        if isinstance(c, tuple):
            chars_map.append(c)
        else:
            chars_map.append((c, c))
    for old_char, new_char in chars_map:
        text = text.replace(old_char, new_char)
    return text


def remove_words_with_numbers(text):
    words = text.split()
    return ' '.join([
        w for w in words if not re.findall(r'.*[0-9].*', w)
    ])
