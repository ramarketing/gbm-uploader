import os

from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'))


DEBUG = True if os.getenv('DEBUG') == 'True' else False

PDB_DEBUG = True if DEBUG and os.getenv('PDB_DEBUG') == 'True' else False


API_ROOT = os.getenv('API_ROOT')

API_USERNAME = os.getenv('API_USERNAME')

API_PASSWORD = os.getenv('API_PASSWORD')


CAPTCHA_USERNAME = os.getenv('CAPTCHA_USERNAME')

CAPTCHA_PASSWORD = os.getenv('CAPTCHA_PASSWORD')
