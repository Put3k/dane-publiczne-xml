# EXCLUDE FROM RSYNC
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(BASE_DIR / '.env')

BASE_PUBLIC_DATA_PATH = BASE_DIR / 'test'
DEVELOPERS_JSON_PATH = BASE_DIR / 'developers_data.json'
DRIVE_KEYS = BASE_DIR / 'drive_keys'
