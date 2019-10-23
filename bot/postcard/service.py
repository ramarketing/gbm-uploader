from ..base.service import BaseEntity, BaseEntityList, BaseService


class Postcard(BaseEntity):
    def __str__(self):
        return self.username


class PostcardList(BaseEntityList):
    entity = Postcard


class PostcardService(BaseService):
    endpoint = '/panel/seo/postcards/'
    entity = Postcard
    entity_list = PostcardList

    def get_list(self, **kwargs):
        kwargs['account__is_active'] = 2
        kwargs['status'] = 'not-created'
        return super().get_list(**kwargs)
