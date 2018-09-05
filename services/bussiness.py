class Entity:
    def __init__(self, data):
        self.data = data

    def __getattribute__(self, attr):
        try:
            return self.data[attr]
        except IndexError:
            return super().__getattribute__(attr)
