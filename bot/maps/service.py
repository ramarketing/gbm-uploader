import csv
import os

from ..base.service import BaseEntity, BaseEntityList, BaseService


class Map(BaseEntity):
    def __str__(self):
        return self.name


class MapList(BaseEntityList):
    entity = Map


class MapService(BaseService):
    entity = Map
    entity_list = MapList

    def get_list(self, **kwargs):
        folder = os.getcwd()
        for root, dirs, files in os.walk(folder):
            for name in files:
                if not name.endswith('.csv'):
                    continue

                file = os.path.join(folder, name)
                data = [i for i in csv.DictReader(open(file, 'r'))]
                valid_file = True

                for i in data:
                    if 'directions' in i and i['directions']:
                        valid_file = False

                if not valid_file:
                    continue

                print('Running file: "{}".'.format(file))

                data = {
                    'next': None,
                    'previous': None,
                    'count': len(data),
                    'results': data
                }

                return self.entity_list(self, data)
