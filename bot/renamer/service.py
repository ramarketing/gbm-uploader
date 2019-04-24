from bot.base.service import BaseEntity, BaseEntityList, BaseService


class Business(BaseEntity):
    def __str__(self):
        return self.name

    def get_code(self, **kwargs):
        response = self.service.request(
            'post', pk=self.pk, extra='code', data=kwargs
        )
        return response['msg']

    def request(self, method, endpoint=None, pk=None, extra=None, **kwargs):
        self.is_valid_method(method)
        endpoint = self.prepare_endpoint(endpoint=endpoint, pk=pk, extra=extra)
        skip_token = kwargs.pop('skip_token', False)

        if not skip_token and not self.token:
            self.authenticate()

        if 'headers' not in kwargs:
            kwargs['headers'] = self.get_headers()

        return self._request(method, endpoint, **kwargs)


class BusinessList(BaseEntityList):
    entity = Business


class BusinesService(BaseService):
    endpoint = '/renamer/business/'
    entity = Business
    entity_list = BusinessList

    def get_list(self, **kwargs):
        kwargs['is_renamed'] = 3
        kwargs['to_rename'] = 2
        kwargs['is_fail'] = 3
        kwargs['is_success'] = 3
        kwargs['is_validated'] = 3
        return super().get_list(**kwargs)
