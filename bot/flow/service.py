from ..base.service import BaseEntity, BaseEntityList, BaseService


class Business(BaseEntity):
    def __str__(self):
        return self.name


class BusinessList(BaseEntityList):
    entity = Business


class BusinessService(BaseService):
    endpoint = '/renamer/business/'
    entity = Business
    entity_list = BusinessList

    def get_allowed_methods(self):
        return ('get', 'post', 'put')

    def get_list(self, **kwargs):
        kwargs['is_fail'] = 3
        kwargs['is_pending'] = 3
        kwargs['is_success'] = 3
        kwargs['to_rename'] = 3
        kwargs['has_credential'] = 3
        return super().get_list(**kwargs)


class Credential(BaseEntity):
    def __str__(self):
        return self.name


class CredentialList(BaseEntityList):
    entity = Credential


class CredentialService(BaseService):
    endpoint = '/renamer/credentials/'
    entity = Credential
    entity_list = CredentialList

    def get_list(self, **kwargs):
        kwargs['is_fail'] = 3
        kwargs['is_success'] = 3
        return super().get_list(**kwargs)
