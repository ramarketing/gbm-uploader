import sys

from uploader import Uploader


if __name__ == '__main__':
    Uploader(sys.argv[1:]).handle()
