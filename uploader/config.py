import os

from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'))

DEBUG = True if os.getenv('DEBUG', False) == 'True' else False

PDB_DEBUG = True if os.getenv('PDB_DEBUG', False) == 'True' else False

API_ROOT = os.getenv('API_ROOT')

API_USERNAME = os.getenv('API_USERNAME')

API_PASSWORD = os.getenv('API_PASSWORD')

PER_CREDENTIAL = int(os.getenv('PER_CREDENTIAL'))

WAIT_TIME = int(os.getenv('WAIT_TIME'))
