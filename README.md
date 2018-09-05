# Google Business Manager Uploader

This Python script allows you to upload CSV files with business to Google Business Manager.

## Requirements
* Windows
* [git for Windows](https://github.com/git-for-windows/git/releases/download/v2.18.0.windows.1/Git-2.18.0-64-bit.exe) - Make sure to select: use git bash on Windows MS-DOS shell.
* [Python 3.7.0](https://www.python.org/downloads/release/python-370/) - Make sue to select: Add to system `$PATH`.

## Running the script
1. Go to the desired folder
```shell
git clone https://github.com/tiptomarketing/gbm-uploader.git
cd gbm-uploader
```

2. (Optional) Install and activate your `virtualenv`
```shell
pip install virtualenv
env\Scrips\activate
```

3. Install Python Requirements
```shell
pip install -r requirements.txt
```

4. Create your `.env` file, change it and save it.
```shell
cp .env.save .env
nano .env
```

5. Add a credentials file named `1.xlsx` to folder `logins/`

6. Add the `csv` files to folder `csv/`

7. Run the script with the command
```shell
env\Scrips\activate
python uploader.py <username> <password>
```
