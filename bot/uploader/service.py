from base.service import BaseEntity, BaseEntityList, BaseService


class Business(BaseEntity):
    def __str__(self):
        return self.name


class BusinessList(BaseEntityList):
    entity = Business


class BusinessService(BaseService):
    endpoint = '/renamer/business/'
    entity = Business
    entity_list = BusinessList


class Credential(BaseEntity):
    def __str__(self):
        return self.email


class CredentialList(BaseEntityList):
    entity = Credential


class CredentialService(BaseService):
    endpoint = '/mixer/credentials/'
    entity = Credential
    entity_list = CredentialList
