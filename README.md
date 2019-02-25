# Google Business Manager Uploader

This Python script allows you to upload CSV files with business to Google Business Manager.

## Requirements
* Windows
* [git for Windows](https://github.com/git-for-windows/git/releases/download/v2.18.0.windows.1/Git-2.18.0-64-bit.exe) - Make sure to select: use git bash on Windows MS-DOS shell.
* [Python 3.7.0](https://www.python.org/downloads/release/python-370/) - Make sue to select: Add to system `$PATH`.

## Installing the script
1. Go to the desired folder
```shell
git clone https://github.com/ramarketing/gbm-uploader.git
cd gbm-uploader
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

4. Create your `.env` file, change it and save it.
```shell
copy uploader\.env.save uploader\.env
notepad uploader\.env
```

5. Type the information provided, save and close.

## Running the script

```shell
cd ~/Sites/gbm-uploader  # Recommended path
env\Scripts\activate
python uploader
```

## Optional arguments
1. You can use the argument "city" to obtain results on a specific city.

```shell
python manage.py city="Los Angeles"
```

The above command will only upload businesses from "Los Angeles".

2. You can use the argument "max" in case you only want N success businesses.

```shell
python manage.py max=10
```

The above command will stop after finding 10 success businesses.

3. You can combine both arguments

```shell
python manage.py city="Los Angeles" max=10
```

The above command will stop after finding 10 success businesses on "Los Angeles".
