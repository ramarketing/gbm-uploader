import bot


def main(*args, **kwargs):
    print(args, kwargs)
    bot.run(*args, **kwargs)
