import sys

from uploader import Uploader


if __name__ == '__main__':
    kwargs = {}
    for kwarg in sys.argv[1:]:
        k, v = kwarg.split('=')
        kwargs[k] = v
    Uploader().handle(**kwargs)
