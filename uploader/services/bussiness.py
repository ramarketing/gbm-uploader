from datetime import datetime
import csv
import os

from config import BASE_DIR
from exceptions import EmptyUpload
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
            if field and hasattr(self, field):
                value = getattr(self, field)
            else:
                value = ''
            line.append('{}'.format(value))

        return line

    def report_success(self, credential):
        if self.date_success:
            return False
        self.update(date_success=datetime.now())
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
                if any([biz.date_success, biz.date_fail]):
                    continue
                writer.writerow(biz.get_csv_line(counter))
                counter += 1

            if counter == 1:
                raise EmptyUpload
        return path

    def get_by_name(self, value):
        return self.get_by('name', value)


class BusinessService(BaseService):
    endpoint = '/mixer/business/'
    entity = Business
    entity_list = BusinessList
