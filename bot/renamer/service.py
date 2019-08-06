from datetime import datetime

from ..base.service import BaseEntity, BaseEntityList, BaseService


class Business(BaseEntity):
    def __str__(self):
        return self.name

    def get_code(self, **kwargs):
        response = self.service.request(
            'post', pk=self.pk, extra='code', data=kwargs
        )
        return response['msg']

    def report_pending(self):
        if self.date_pending:
            return False
        self.update(date_pending=datetime.now())
        return self.service.request('post', pk=self.pk, extra='set-pending')


class BusinessList(BaseEntityList):
    entity = Business


class BusinessService(BaseService):
    endpoint = '/renamer/business/'
    entity = Business
    entity_list = BusinessList

    def get_list(self, **kwargs):
        kwargs['is_fail'] = 3
        kwargs['is_pending'] = 3
        kwargs['is_success'] = 3
        kwargs['to_rename'] = 2
        return super().get_list(**kwargs)
