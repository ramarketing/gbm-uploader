from services.base import (
    BaseEntity, BaseEntityList, BaseService
)


class Credential(BaseEntity):
    def __str__(self):
        return self.name


class CredentialList(BaseEntityList):
    entity = Credential


class CredentialService(BaseService):
    endpoint = '/mixer/credentials/'
    entity = Credential
    entity_list = CredentialList

    def get_list(self, **kwargs):
        if 'can_use' not in kwargs:
            kwargs['can_use'] = 1
        return super().get_list(**kwargs)
