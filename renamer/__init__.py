from base.service import BaseEntity, BaseEntityList, BaseService


class Business(BaseEntity):
    def __str__(self):
        return self.name


class BusinessList(BaseEntityList):
    entity = Business


class BusinesService(BaseService):
    endpoint = '/renamer/business/'
    entity = Business
    entity_list = BusinessList
