import json

from datetime import datetime
from urllib.parse import urlparse, parse_qs

import requests

from .. import config
from ..logger import Logger


logging = Logger()


class Entity:
    def __eq__(self, other):
        return False

    def __init__(self, data):
        assert isinstance(data, dict), (
            "%s Data must be a dict instance." % self.__class__.__name__
        )
        self.raw_data = data

    def __getattr__(self, name):
        try:
            value = self.raw_data[name]
            if isinstance(value, dict):
                return Entity(value)
            else:
                return value
        except (KeyError, IndexError):
            return self.__getattribute__(name)


class BaseEntity(Entity):
    def __eq__(self, other):
        return self.pk == other.pk

    def __init__(self, service, data):
        super().__init__(data)
        self.service = service

    def delete(self):
        return self.service.request('delete', pk=self.pk)

    @property
    def pk(self):
        return self.id

    def patch(self, **kwargs):
        self.update(**kwargs)
        return self.service.request('patch', pk=self.pk, data=kwargs)

    def put(self, **kwargs):
        self.update(**kwargs)
        return self.service.request('put', pk=self.pk, data=kwargs)

    def refresh(self):
        return self.service.get_detail(self.pk)

    def report_fail(self):
        if self.date_fail:
            return False
        self.update(date_fail=datetime.now())
        return self.service.request('post', pk=self.pk, extra='set-fail')

    def report_success(self, **kwargs):
        if self.date_success:
            return False
        self.update(date_success=datetime.now())
        return self.service.request(
            'post', pk=self.pk, extra='set-success', data=kwargs
        )

    def update(self, **kwargs):
        for k in kwargs:
            self.raw_data[k] = kwargs[k]


class BaseEntityList:
    entity_list = []

    def __init__(self, service, data):
        assert isinstance(data, dict), (
            "%s: Data must be a dict instance." % self.__class__.__name__
        )
        self.service = service
        self.prepare_data(data)

    def prepare_data(self, data):
        self.raw_data = data
        self.total_count = self.raw_data['count']
        self.next = self.raw_data['next']
        self.previous = self.raw_data['previous']

        self.entity_list = [
            self.entity(self.service, item)
            for item in self.raw_data['results']
        ]

    def __getitem__(self, key):
        return self.entity_list[key]

    @property
    def count(self):
        return len(self.entity_list)

    def get_by(self, name, value):
        for biz in self:
            if getattr(biz, name) == value:
                return biz

    def get_by_pk(self, value):
        return self.get_by('pk', value)

    def get_next_page(self):
        assert self.next, (
            "%s: Next page not exists." % self.__class__.__name__
        )
        params = self.service.get_url_params(self.next)
        r = self.service.get_list(**params)
        self.prepare_data(r.raw_data)

    def get_previous_page(self):
        assert self.previous, (
            "%s: Previous page not exists." % self.__class__.__name__
        )
        params = self.service.get_url_params(self.previous)
        r = self.service.get_list(**params)
        self.prepare_data(r.raw_data)


class BaseService:
    allowed_methods = ('get', 'post')
    entity = BaseEntity
    entity_list = BaseEntityList
    errors = {
        'api_root': "%s: An API base endpoint is required.",
        'credentials': "%s: A username/password combo is required.",
    }
    token = None

    def authenticate(self):
        assert not self.token, (
            "%s: A token was found." % self.__class__.__name__
        )
        data = dict(
            username=config.API_USERNAME,
            password=config.API_PASSWORD,
        )
        r = self.request('post', 'account/login/', data=data, skip_token=True)
        self.token = r['token']

    def create(self, **kwargs):
        r = self.request('post', data=kwargs)
        return self.entity(self, r)

    def get_headers(self):
        if self.token:
            return {
                'Authorization': 'Token {}'.format(self.token),
            }
        return {}

    def get_allowed_methods(self):
        return self.allowed_methods

    def get_list(self, **kwargs):
        r = self.request('get', params=kwargs)
        return self.entity_list(self, r)

    def get_detail(self, pk):
        r = self.request('get', pk=pk)
        return self.entity(self, r)

    def get_url_params(self, url):
        url = urlparse(url)
        return parse_qs(url.query)

    def is_valid_method(self, method, raise_exeception=True):
        return True

    def prepare_endpoint(self, endpoint=None, pk=None, extra=None):
        url = config.API_ROOT
        endpoint = endpoint or self.endpoint
        assert endpoint, (
            "%s: Invalid endpoint" % self.__class__.__name__
        )

        if url.endswith('/'):
            url = url[:-1]

        if not endpoint.startswith('/'):
            url += '/' + endpoint
        else:
            url += endpoint

        if not url.endswith('/'):
            url += '/'

        if pk:
            url += '{}/'.format(pk)

        if extra:
            url += '{}/'.format(extra)

        return url

    def request(self, method, endpoint=None, pk=None, extra=None, **kwargs):
        self.is_valid_method(method)
        endpoint = self.prepare_endpoint(endpoint=endpoint, pk=pk, extra=extra)
        skip_token = kwargs.pop('skip_token', False)

        if not skip_token and not self.token:
            self.authenticate()

        if 'headers' not in kwargs:
            kwargs['headers'] = self.get_headers()

        return self._request(method, endpoint, **kwargs)

    def _request(self, method, endpoint, **kwargs):
        log_kwargs = kwargs.copy()
        if 'headers' in log_kwargs:
            log_kwargs.pop('headers')
        logging(instance=self.__class__, data={
            'method': method,
            'endpoint': endpoint,
            'data': log_kwargs
        })
        r = getattr(requests, method)(endpoint, **kwargs)
        assert r.status_code >= 200 and r.status_code < 300, (
            "%s: Request error: %s" % (self.__class__.__name__, r.json())
        )
        try:
            response = r.json()
        except json.decoder.JSONDecodeError:
            response = r.content
        logging(instance=self.__class__, data=response)
        return response
