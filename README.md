# Google Business Manager Uploader

This Python script allows you to upload CSV files with business to Google Business Manager.

## Requirements
* Windows
* [git for Windows](https://github.com/git-for-windows/git/releases/download/v2.18.0.windows.1/Git-2.18.0-64-bit.exe) - Make sure to select: use git bash on Windows MS-DOS shell.
* [Python 3.7.0](https://www.python.org/downloads/release/python-374/) - Make sure to select: Add to system `$PATH`.

## Installing the script
1. Go to the desired folder
```shell
git clone https://github.com/ramarketing/gbm-uploader.git
cd gbm-uploader
git checkout renamer
```

2. (Optional) Install and activate your `virtualenv`
```shell
pip install virtualenv
virtualenv env
env\Scripts\activate
```

3. Install Python Requirements
```shell
pip install -r requirements.txt
```


## Running the script

```shell
cd ~/Sites/gbm-uploader  # Recommended path
env\Scripts\activate
python bot maps
```
