import csv
from datetime import datetime
import os
import re

from .selenium import MapsSelenium


def validate_cid(value):
    pattern = re.compile(r'http(s)?:\/\/(www\.)?google\.com\/maps\?cid=\d{20}')
    if not pattern.match(value):
        raise ValueError(f'Invalid value: "{value}"')


def slugify(value):
    value = str(value)
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)


def run(*args, **kwargs):
    now = datetime.now()

    filename = kwargs.get('--file', None)
    if filename is None:
        print('--file attribute is required.')
        return

    filepath = os.path.join(os.getcwd(), filename)
    source = open(filepath, 'r+')
    reader = csv.DictReader(source)
    cid_list = []
    for index, row in enumerate(reader):
        assert all([row['cid'], row['metro area'], row['state']])
        validate_cid(row['cid'])
        cid_list.append(row)

    cid_updated = []
    for cid in cid_list:
        selenium = MapsSelenium(cid=cid)
        cid_updated.append(
            selenium()
        )

    source.seek(0)
    writer = csv.DictWriter(source, fieldnames=cid_updated[0].keys())
    writer.writeheader()
    for cid in cid_updated:
        writer.writerow(cid)
    source.truncate()
    source.close()

    for cid in cid_updated:
        filename = now.strftime(
            f'{slugify(cid["name"])}-%Y-%M-%d-%H-%M-%S.csv'
        )
        file = open(os.path.join(os.getcwd(), filename), 'w+')
        selenium = MapsSelenium(cid=cid, file=file)
        selenium()
        file.close()
