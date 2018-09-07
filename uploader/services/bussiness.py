import csv
import os

from config import BASE_DIR
from services.base import (
    BaseEntity, BaseEntityList, BaseService
)
from constants import CSV_FIELDS, CSV_HEADER


class Business(BaseEntity):
    def __str__(self):
        return self.name

    def get_csv_line(self, counter):
        line = []
        for field in CSV_FIELDS:
            if field == 'id':
                value = counter
            elif field and hasattr(self, field):
                value = getattr(self, field)
            else:
                value = ''
            line.append('{}'.format(value))

        return line

    def report_success(self, credential):
        data = dict(
            credential=credential.pk
        )
        return self.service.request(
            'post', pk=self.pk, extra='set-success', data=data
        )


class BusinessList(BaseEntityList):
    entity = Business

    def create_csv(self):
        path = os.path.join(BASE_DIR, 'csv/gbm.csv')
        with open(path, 'w') as file:
            counter = 1
            writer = csv.writer(file)
            writer.writerow(CSV_HEADER)

            for biz in self:
                writer.writerow(biz.get_csv_line(counter))
                counter += 1
        return path

    def get_by_name(self, value):
        return self.get_by('name', value)


class BusinessService(BaseService):
    endpoint = '/mixer/business/'
    entity = Business
    entity_list = BusinessList

    def get_list(self, **kwargs):
        if 'can_use' not in kwargs:
            kwargs['can_use'] = 1
        if 'limit' not in kwargs:
            kwargs['limit'] = 9
        return super().get_list(**kwargs)
