# EXCLUDE FROM RSYNC
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(BASE_DIR / '.env')

HTTP_HOST = os.environ['HTTP_HOST']
BASE_PUBLIC_DATA_PATH = BASE_DIR / 'test'
DEVELOPERS_JSON_PATH = BASE_DIR / 'developers_data.json'
DRIVE_KEYS = BASE_DIR / 'drive_keys'

# SMTP run-summary notifications (secrets come from the environment, never git)
SMTP_HOST = os.environ.get('SMTP_HOST', 'localhost')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM = os.environ.get('SMTP_FROM', '')
SMTP_TO = os.environ.get('SMTP_TO', '')  # comma-separated recipients
