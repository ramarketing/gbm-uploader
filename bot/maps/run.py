import csv
import os

from config import BASE_DIR

from maps.selenium import MapsSelenium
from maps.service import MapService


def run(*args, **kwargs):
    maps_service = MapService()
    object_list = maps_service.get_list()

    for obj in object_list:
        MapsSelenium(entity=obj)

    with open(os.path.join(BASE_DIR, 'file.csv'), 'w') as file:
        obj = object_list[0]

        fieldnames = [h for h in obj.raw_data.keys()]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for obj in object_list:
            writer.writerow(obj.raw_data)
    file.close()
