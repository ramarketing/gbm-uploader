import csv
import os

from config import BASE_DIR
from base.service import BaseEntity, BaseEntityList, BaseService


class Map(BaseEntity):
    def __str__(self):
        return self.name


class MapList(BaseEntityList):
    entity = Map


class MapService(BaseService):
    entity = Map
    entity_list = MapList

    def get_list(self, **kwargs):
        file = os.path.join(BASE_DIR, 'file.csv')
        data = [i for i in csv.DictReader(open(file, 'r'))]

        data = {
            'next': None,
            'previous': None,
            'count': len(data),
            'results': data
        }

        return self.entity_list(self, data)
