from ..base.service import BaseEntity, BaseEntityList, BaseService


class GMB(BaseEntity):
    def __str__(self):
        return self.name


class GMBList(BaseEntityList):
    entity = GMB


class GMBService(BaseService):
    endpoint = '/panel/seo/gmbs/'
    entity = GMB
    entity_list = GMBList

    def get_allowed_methods(self):
        return ('get', 'post', 'put')

    def get_list(self, **kwargs):
        kwargs['has_api_id'] = 3
        return super().get_list(**kwargs)


class Account(BaseEntity):
    def __str__(self):
        return self.username


class AccountList(BaseEntityList):
    entity = Account


class AccountService(BaseService):
    endpoint = '/panel/seo/accounts/'
    entity = Account
    entity_list = AccountList

    def get_list(self, **kwargs):
        kwargs['is_active'] = 2
        kwargs['has_password'] = 2
        kwargs['provider'] = 'google'
        return super().get_list(**kwargs)
