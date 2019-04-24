import sys

from bot.renamer.run import run


if __name__ == '__main__':
    kwargs = {}
    for kwarg in sys.argv[1:]:
        k, v = kwarg.split('=')
        kwargs[k] = v
    run(**kwargs)
