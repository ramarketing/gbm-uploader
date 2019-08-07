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
            writer = csv.DictWriter(file, fieldnames=[
                'Location',
                'Name',
                'Business',
                'Description',
                'Directions',
                'Related Searches'
            ])
            writer.writeheader()

            for obj in object_list:
                data = dict(
                    location=obj.location,
                    name='{main_keyword} {city} - {name}'.format(
                        main_keyword=obj.main_keyword,
                        city=obj.location_city,
                        name=obj.name
                    ),
                    business=(
                        '{name}\n{address}\n{phone}\n{url}\n{cid_url}'
                    ).format(
                        name=obj.name,
                        address=obj.address,
                        phone=obj.phone,
                        url=obj.url,
                        cid_url=obj.cid_url
                    ),
                    description=obj.description,
                    directions=obj.directions,
                    related_searches=obj.related_keywords
                )
                writer.writerow(data)

        file.close()
