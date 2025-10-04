#!/usr/bin/env python3
'''
download_drive_csv.py

Plik service account JSON powinien być pobrany z Google Cloud Console.
Plik na Drive musi być udostępniony (viewer) temu service account email.
'''

import io
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
API_SERVICE = 'drive'
API_VERSION = 'v3'

def download_file(sa_json_path, file_id, out_path):
    creds = service_account.Credentials.from_service_account_file(
        sa_json_path, scopes=SCOPES
    )
    service = build(
        API_SERVICE, API_VERSION, credentials=creds, cache_discovery=False
    )

    try:
        request = service.files().export(fileId=file_id, mimeType='text/csv')
        fh = io.FileIO(out_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                # pokazujemy postęp (0.0 - 1.0)
                pct = int(status.progress() * 100)
                print(f"Postęp: {pct}%")
        print(f"Pobrano plik i zapisano do: {out_path}")

    except HttpError as e:
        print("Błąd HTTP przy pobieraniu pliku:", e, file=sys.stderr)
        raise
    except Exception as e:
        print("Nieoczekiwany błąd:", e, file=sys.stderr)
        raise


if __name__ == '__main__':
    from datetime import datetime
    from pathlib import Path
    today = datetime.today()

    path = f'/home/dane-publiczne/data/dane-publiczne/{today.strftime("%Y/%m")}'
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

    file_name = f'arcus-{today.day}.csv'
    file_path = path / file_name

    download_file(
        sa_json_path='/home/dane-publiczne/script/pod-manage-db493003b6e1.json',
        file_id='1PtFy7D19QbFlH5sBajwTNrDj6MCLFjct3EaijxzctNo',
        out_path=file_path
    )

