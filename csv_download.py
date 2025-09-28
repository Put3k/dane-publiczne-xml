#!/usr/bin/env python3
"""
download_drive_csv.py

Pobiera prywatny plik (np. CSV) z Google Drive używając service account.
Użycie:
  ./download_drive_csv.py --key /path/to/sa-key.json --file-id FILE_ID --out /tmp/data.csv

Plik service account JSON powinien być pobrany z Google Cloud Console.
Plik na Drive musi być udostępniony (viewer) temu service account email.
"""

import io
import argparse
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
API_SERVICE = 'drive'
API_VERSION = 'v3'

def download_file(sa_json_path: str, file_id: str, out_path: str):
    creds = service_account.Credentials.from_service_account_file(
        sa_json_path, scopes=SCOPES
    )
    service = build(
        API_SERVICE, API_VERSION, credentials=creds, cache_discovery=False
    )

    try:
        # Pobieramy zawartość pliku (works for binary files stored on Drive, e.g. CSV)
        # request = service.files().get_media(fileId=file_id)
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


def main():
    p = argparse.ArgumentParser(
        description="Pobierz plik z Google Drive (service account)"
    )
    p.add_argument(
        '--key', required=True, help='Ścieżka do JSON key service account'
    )
    p.add_argument(
        '--file-id',
        required=True,
        help='ID pliku na Google Drive (długie id w URL)',
    )
    p.add_argument(
        '--out', required=True, help='Ścieżka docelowa zapisu, np /tmp/data.csv'
    )
    args = p.parse_args()
    download_file(args.key, args.file_id, args.out)


if __name__ == '__main__':
    # main()
    download_file(
        sa_json_path='/home/kacper/projects/dane-publiczne/pod-manage-db493003b6e1.json',
        file_id='1PtFy7D19QbFlH5sBajwTNrDj6MCLFjct3EaijxzctNo',
        out_path='/home/kacper/projects/dane-publiczne/result.csv'
    )

