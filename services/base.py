import os


class Entity:
    def __init__(self, data):
        self.data = data

    def __getattribute__(self, attr):
        try:
            return self.data[attr]
        except IndexError:
            return super().__getattribute__(attr)


class EntityList:
    pass


class Service:
    API_ROOT = os.getenv('API_ROOT')

    def __init__(self, endpoint):
        self.endpoint = self.API_ROOT + endpoint

    def
