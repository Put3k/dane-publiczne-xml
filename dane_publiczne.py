import os
from csv_download import download_file
from datetime import datetime


if __name__ == '__main__':
    #INFO: fetch csv from drive
    base_path_public_path = '/home/kacper/projects/dane-publiczne'
    today = datetime.today().strftime('%Y-%m-%d')
    file_name = f'ceny-ofertowe-mieszkan-dewelopera-arcus-{today}.csv'
    file_path = os.path.join(base_path_public_path, file_name)
    download_file(
        sa_json_path='/home/kacper/projects/dane-publiczne/pod-manage-db493003b6e1.json',
        file_id='1PtFy7D19QbFlH5sBajwTNrDj6MCLFjct3EaijxzctNo',
        out_path=file_path,
    )

    #INFO: Load existing XML
    xml_file_path = '/home/kacper/projects/dane-publiczne/Szablon_budowy_pliku_xml_v.1.13_21.08.2025.xml'
    pass
    # create new resource for today
