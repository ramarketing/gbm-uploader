from datetime import datetime
import os

from services.base import (
    BaseEntity, BaseEntityList, BaseService
)


class Credential(BaseEntity):
    def __str__(self):
        return self.email

    def report_success(self):
        if self.date_success:
            return False
        self.update(date_success=datetime.now())
        return self.service.request('post', pk=self.pk, extra='set-success')


class CredentialList(BaseEntityList):
    entity = Credential


class CredentialService(BaseService):
    endpoint = '/mixer/credentials/'
    entity = Credential
    entity_list = CredentialList

    def get_list(self, **kwargs):
        if 'can_use' not in kwargs:
            kwargs['can_use'] = 1
        if 'limit' not in kwargs:
            kwargs['limit'] = os.getenv('CREDENTIALS', 10)
        return super().get_list(**kwargs)
