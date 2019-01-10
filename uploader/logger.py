from datetime import datetime
import os

from config import BASE_DIR, DEBUG


class UploaderLogger:
    def __init__(self, filename='uploader'):
        assert isinstance(filename, str), "Filename must be a string instace."
        if not filename.endswith('.log'):
            filename = '{}.log'.format(filename)
        self.file = os.path.join(BASE_DIR, filename)

    def __call__(self, data=None, instance=None):
        if instance:
            class_ = instance.__class__.__name__
        else:
            class_ = 'NO_CLASS'

        line = "[{datetime}] [{class_}] {instance} - {message}".format(
            class_=class_,
            datetime=datetime.now().strftime('%c'),
            instance=str(instance) if instance else '',
            message=str(data) if data else '',
        )
        self.append_to_file(line)

    def append_to_file(self, line):
        with open(self.file, 'a') as file:
            if DEBUG:
                print(line)
            file.write('\n' + line)
