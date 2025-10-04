import os
from datetime import datetime
from pathlib import Path

from csv_download import download_file

# BASE_CSV_PUBLIC_PATH = Path('/home/dane-publiczne/data/dane-publiczne')
BASE_CSV_PUBLIC_PATH = Path('/home/dane-publiczne/data/dane-publiczne')


def csv_public_url_get(file_path):
    host = 'kw.db.test.pl'
    # host = os.environ['HTTP_HOST']
    # if not host:
    #     raise ValueError('missing HTTP_HOST env variable')
    url = f'{host}/{file_path}'
    return url

if __name__ == '__main__':
    #INFO: fetch csv from drive
    today = datetime.today()
    
    relative_ym_path = today.strftime("%Y/%m")
    abs_dir_path = BASE_CSV_PUBLIC_PATH / relative_ym_path
    # abs_dir_path.mkdir(parents=True, exist_ok=True)

    file_name = f'arcus-{today.day}.csv'
    print(csv_public_url_get(f'{relative_ym_path}/{file_name}'))

    download_dest_path = BASE_CSV_PUBLIC_PATH / relative_ym_path / file_name
    #
    # download_file(
    #     sa_json_path='/home/dane-publiczne/script/pod-manage-db493003b6e1.json',
    #     file_id='1PtFy7D19QbFlH5sBajwTNrDj6MCLFjct3EaijxzctNo',
    #     out_path=file_path
    # )


    #INFO: Load existing XML
    xml_file_path = '/home/kacper/projects/dane-publiczne/Szablon_budowy_pliku_xml_v.1.13_21.08.2025.xml'
    pass
    # create new resource for today
