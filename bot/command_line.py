import sys

from .flow.run import run as flow_bot
from .login.run import run as login_bot
from .maps.run import run as maps_bot
from .uploader.run import run as uploader_bot
from .renamer.run import run as renamer_bot
from .porch.run import run as porch_bot
from .postcard.run import run as postcard_bot


def main(*args, **kwargs):
    bot = sys.argv[1]

    if bot == 'flow':
        run = flow_bot
    elif bot == 'login':
        run = login_bot
    elif bot == 'renamer':
        run = renamer_bot
    elif bot == 'uploader':
        run = uploader_bot
    elif bot == 'maps':
        run = maps_bot
    elif bot == 'porch':
        run = porch_bot
    elif bot == 'postcard':
        run = postcard_bot
    else:
        raise NotImplementedError(
            "Invalid bot. \"%s\" doesn't exists." % bot
        )

    kwargs = {}

    for kwarg in sys.argv[2:]:
        try:
            k, v = kwarg.split('=')
            kwargs[k] = v
        except ValueError:
            continue

    print('Running bot "%s" with arguments "%s"' % (bot, kwargs))
    run(**kwargs)
