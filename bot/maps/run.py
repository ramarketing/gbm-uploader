import csv
import os

from .selenium import MapsSelenium
from .service import MapService


def run(*args, **kwargs):
    folder = os.getcwd()
    for name in os.listdir(folder):
        if (
            not os.path.isfile(os.path.join(folder, name)) or
            not name.endswith('.csv')
        ):
            continue

        file_name = os.path.join(folder, name)
        maps_service = MapService()
        object_list = maps_service.get_list(file=file_name)

        if not object_list:
            continue

        for obj in object_list:
            MapsSelenium(entity=obj)

        with open(file_name, 'w') as file:
            obj = object_list[0]

            fieldnames = [h for h in obj.raw_data.keys()]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

            for obj in object_list:
                writer.writerow(obj.raw_data)

        file.close()
