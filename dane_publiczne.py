import hashlib
import os
import json
from datetime import datetime

from lxml import etree as ET

from csv_download import download_file
from settings import (
    BASE_PUBLIC_DATA_PATH,
    DEVELOPERS_JSON_PATH,
    DRIVE_KEYS,
)
from xml_utils import Resource, validate_xml_against_schema


def file_md5_checksum(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def csv_public_url_get(file_path):
    host = os.environ['HTTP_HOST']
    if not host:
        raise ValueError('missing HTTP_HOST env variable')
    url = f'{host}/{file_path}'
    return url


def developer_data_get(developer_code):
    with open(DEVELOPERS_JSON_PATH, 'r') as f:
        f_str = f.read()
        data = json.loads(f_str)[developer_code.upper()]
    return data


def developer_data_generate(developer_code):
    today = datetime.today().date()
    code = developer_code.lower()
    dev_data = developer_data_get(code)

    # INFO: Paths
    relative_ym_path = today.strftime('%Y/%m')
    abs_dir_path = BASE_PUBLIC_DATA_PATH / relative_ym_path
    abs_dir_path.mkdir(parents=True, exist_ok=True)

    # INFO: Download
    file_name = f'{code}-{today.day}.csv'
    download_dest_path = BASE_PUBLIC_DATA_PATH / relative_ym_path / file_name
    download_file(
        sa_json_path=DRIVE_KEYS / dev_data['sa_file_name'],
        file_id=dev_data['csv_file_id'],
        out_path=download_dest_path,
    )
    csv_url = csv_public_url_get(f'dane-publiczne/{relative_ym_path}/{file_name}')

    # INFO: XML
    #TODO: MVP - if xml does not exist, create and fill using BASE.xml
    xml_filename = f'{code.upper()}.xml'
    xml_public_path = BASE_PUBLIC_DATA_PATH / xml_filename
    tree = ET.parse(xml_public_path)
    root = tree.getroot()

    resources = root.find('.//resources')
    if resources is None:
        msg = 'No resources in ElementTree'
        raise ValueError(msg)

    iso_date = today.isoformat()
    new_resource = Resource(
        status='published',
        extIdent=iso_date,
        url=csv_url,
        title_pl=f'Ceny ofertowe mieszkań dewelopera {dev_data["name"]} {iso_date}',
        title_en=f'Offer prices for developer\'s apartments {dev_data["name"]} {iso_date}',
        description_pl=f'Dane dotyczące cen ofertowych mieszkań {dev_data["name"]} z dnia {iso_date}.',
        description_en=f'Data on offer prices of apartments {dev_data["name"]} as of {iso_date}.',
        availability='local',
        dataDate=iso_date,
        specialSigns=['X'],
        hasDynamicData=False,
        hasHighValueData=True,
        hasHighValueDataFromEuropeanCommissionList=False,
        hasResearchData=False,
        containsProtectedData=False,
    )
    resource_element = new_resource.to_etree_element()
    resources.append(resource_element)

    ET.indent(root, space='    ')
    validate_xml_against_schema(tree)

    tree.write(xml_public_path, encoding='utf-8', xml_declaration=True)

    # INFO: checksum
    checksum = file_md5_checksum(xml_public_path)
    checksum_filename = f'{code}.md5'
    checksum_public_path = BASE_PUBLIC_DATA_PATH / checksum_filename
    with open(checksum_public_path, 'w') as f:
        f.write(checksum)


def main():
    for code in ['ARCUS', 'KAKTUS']:
        developer_data_generate(code)


if __name__ == '__main__':
    #TODO: add logging
    os.environ['HTTP_HOST'] = 'https://test.website.pl'
    t_marker = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    print(f'{t_marker} - START')
    main()
    print(f'{t_marker} - FINISH')
