import hashlib
import os
from datetime import datetime
from pathlib import Path

from lxml import etree as ET

from csv_download import download_file
from xml_utils import Resource, validate_xml_against_schema

SA_PATH = Path(
    '/home/kacper/projects/dane-publiczne/pod-manage-db493003b6e1.json'
)
CSV_FILE_ID='1PtFy7D19QbFlH5sBajwTNrDj6MCLFjct3EaijxzctNo'
BASE_PUBLIC_DATA_PATH = Path('/home/kacper/projects/dane-publiczne/test')
XML_PATH = Path('/home/kacper/projects/dane-publiczne/test/ARCUS.xml')
DEVELOPER_DATA = dict(name='Arcus Development Sp. z o.o.', id='ARCUS')

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


def main():
    today = datetime.today().date()

    # INFO: Paths
    relative_ym_path = today.strftime('%Y/%m')
    abs_dir_path = BASE_PUBLIC_DATA_PATH / relative_ym_path
    abs_dir_path.mkdir(parents=True, exist_ok=True)

    # INFO: Download
    file_name = f'arcus-{today.day}.csv'
    download_dest_path = BASE_PUBLIC_DATA_PATH / relative_ym_path / file_name
    download_file(
        sa_json_path=SA_PATH,
        file_id=CSV_FILE_ID,
        out_path=download_dest_path,
    )
    csv_url = csv_public_url_get(f'{relative_ym_path}/{file_name}')

    # INFO: XML
    tree = ET.parse(XML_PATH)
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
        title_pl=f'Ceny ofertowe mieszkań dewelopera {DEVELOPER_DATA["name"]} {iso_date}',
        title_en=f'Offer prices for developer\'s apartments {DEVELOPER_DATA["name"]} {iso_date}',
        description_pl=f'Dane dotyczące cen ofertowych mieszkań {DEVELOPER_DATA["name"]} z dnia {iso_date}.',
        description_en=f'Data on offer prices of apartments {DEVELOPER_DATA["name"]} as of {iso_date}.',
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

    xml_filename = f'{DEVELOPER_DATA["id"]}.xml'
    xml_public_path = BASE_PUBLIC_DATA_PATH / xml_filename
    tree.write(xml_public_path, encoding='utf-8', xml_declaration=True)

    # INFO: checksum
    checksum = file_md5_checksum(xml_public_path)
    checksum_filename = f'{DEVELOPER_DATA["id"]}.md5'
    checksum_public_path = BASE_PUBLIC_DATA_PATH / checksum_filename
    with open(checksum_public_path, 'w') as f:
        f.write(checksum)


if __name__ == '__main__':
    main()
