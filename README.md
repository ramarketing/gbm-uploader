# Google Business Manager Uploader

This Python script allows you to upload CSV files with business to Google Business Manager.

## Requirements
* Windows
* [GitHub for Windows](https://central.github.com/deployments/desktop/desktop/latest/win32)
* [Python 3.7.0](https://www.python.org/downloads/release/python-374/) - Make sure to select: Add to system `$PATH`.

## Installing the script
1. Clone the repo. Go to *File* > *Clone repository* > Select *URL* and type onto the URL field:
```shell
https://github.com/ramarketing/gbm-uploader.git
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
