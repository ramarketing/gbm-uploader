import os

import dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


dotenv.load_dotenv(
    os.path.join(os.path.normpath(os.getcwd()), '.env')
)


DEBUG = True if os.getenv('DEBUG') == 'True' else False

PDB_DEBUG = True if DEBUG and os.getenv('PDB_DEBUG') == 'True' else False


API_ROOT = os.getenv('API_ROOT', '')

API_USERNAME = os.getenv('API_USERNAME', '')

API_PASSWORD = os.getenv('API_PASSWORD', '')


CAPTCHA_USERNAME = os.getenv('CAPTCHA_USERNAME')

CAPTCHA_PASSWORD = os.getenv('CAPTCHA_PASSWORD')


MAX_RETRIES = os.getenv('MAX_RETRIES', 5)

INSTANCES = os.getenv('INSTANCES', 1)


STATUS_PROCESSING = os.getenv('STATUS_PROCESSING', 36)

STATUS_APPROVED = os.getenv('STATUS_APPROVED', 34)

STATUS_DENY = os.getenv('STATUS_DENY', 35)

WORKERS = int(os.getenv('WORKERS', 1))
