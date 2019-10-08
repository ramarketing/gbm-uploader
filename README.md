# Google Business Manager Uploader

This Python script allows you to upload CSV files with business to Google Business Manager.

## Requirements
* Windows
* [GIT for Windows](https://github.com/git-for-windows/git/releases/latest) - Make sure to select: Add to system `$PATH` at the end of the installation.
* [Python 3.7.0](https://www.python.org/downloads/release/python-374/) - Make sure to select: Add to system `$PATH`.

## Installing the script
1. Run the following command on CMD-DOS:
```shell
pip install -e git+https://github.com/ramarketing/gbm-uploader.git#egg=bot
```

## Running the script

Make sure that you are inside the folder that contains the propper files.

```shell
bot maps

bot flow
```


## Dotenv example
This isn't for all use cases, like `bot flow`, you will need to create a `.env` under the folder that you will run the bot.

```
API_ROOT="https://api.endpoint.io/api"
API_USERNAME="username"
API_PASSWORD="password"

STATUS_PROCESSING=1
STATUS_APPROVED=2
STATUS_DENY=3
```
