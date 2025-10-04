from datetime import datetime
from pathlib import Path

from csv_download import download_file

if __name__ == '__main__':
    #INFO: fetch csv from drive
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


    #INFO: Load existing XML
    xml_file_path = '/home/kacper/projects/dane-publiczne/Szablon_budowy_pliku_xml_v.1.13_21.08.2025.xml'
    pass
    # create new resource for today
