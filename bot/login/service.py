from ..base.service import BaseEntity, BaseEntityList, BaseService


class GMBTask(BaseEntity):
    def __str__(self):
        return self.username


class GMBTaskList(BaseEntityList):
    entity = GMBTask


class GMBTaskService(BaseService):
    endpoint = '/panel/seo/gmb-tasks/'
    entity = GMBTask
    entity_list = GMBTaskList

    def get_list(self, **kwargs):
        kwargs['status'] = 'pending'
        return super().get_list(**kwargs)
