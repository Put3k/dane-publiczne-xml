import hashlib
import os
import sys
import json
import logging
import traceback
from logging.handlers import RotatingFileHandler
from datetime import datetime

from lxml import etree as ET

from csv_download import download_file
from mailer import Status, DeveloperResult, send_run_summary
from settings import (
    BASE_PUBLIC_DATA_PATH,
    DEVELOPERS_JSON_PATH,
    DRIVE_KEYS,
    BASE_DIR
)
from xml_utils import (
    Resource,
    Dataset,
    resource_exists,
    dataset_find,
    validate_xml_against_schema,
)


log_handler = RotatingFileHandler(
    filename=BASE_DIR / 'cache/dane-publiczne.log',
    mode='a',
    maxBytes=5 * 1024 * 1024,
    backupCount=4,
    encoding='utf-8',
)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)

logger = logging.getLogger('root')
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)



logging.basicConfig(
    filename='cache/dane-publiczne.log', encoding='utf-8', level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


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


def developer_list_get():
    #TODO: DRY
    with open(DEVELOPERS_JSON_PATH, 'r') as f:
        f_str = f.read()
        data = json.loads(f_str)
    return data.keys()


def developer_data_get(developer_code):
    #TODO: DRY
    with open(DEVELOPERS_JSON_PATH, 'r') as f:
        f_str = f.read()
        data = json.loads(f_str)[developer_code.upper()]
    return data


def developer_data_generate(developer_code, date=datetime.today().date()):
    logger.info(f'start processing: {developer_code}')
    code = developer_code.lower()

    # INFO: XML - Load and validate
    #TODO: MVP - if xml does not exist, create and fill using BASE.xml
    xml_filename = f'{code.upper()}.xml'
    xml_public_path = BASE_PUBLIC_DATA_PATH / xml_filename
    tree = ET.parse(xml_public_path)
    datasets = tree.getroot()

    dev_data = developer_data_get(code)

    # INFO: dataset creation if needed - MVP - use xmls data and work on objects
    dataset_identifier = Dataset.ext_ident.format(
        developer_code=developer_code, year=date.year
    )
    if not dataset_find(datasets, dataset_identifier):
        # create dataset dataclass
        new_dataset = Dataset(
            developer_code=developer_code,
            developer_name=dev_data['name'],
            year=date.year,
        )
        datasets.append(new_dataset.to_etree_element())


    # dataset Element
    dataset = dataset_find(datasets, dataset_identifier)
    if dataset is None:
        raise ValueError('Dataset does not exists!')

    resources = dataset.find('./resources')
    if resources is None:
        msg = 'No resources in ElementTree'
        raise ValueError(msg)

    # INFO: Validate resource exists
    iso_date = date.isoformat()
    if resource_exists(resources, iso_date):
        logger.info(
            f'skip processing: {developer_code} - resource "{iso_date}" already exists'
        )
        return Status.SKIPPED

    # INFO: Paths
    relative_ym_path = date.strftime('%Y/%m')
    abs_dir_path = BASE_PUBLIC_DATA_PATH / code / relative_ym_path
    abs_dir_path.mkdir(parents=True, exist_ok=True)

    # INFO: Download
    file_name = f'{date.day}.csv'
    download_dest_path = abs_dir_path / file_name
    download_file(
        sa_json_path=DRIVE_KEYS / dev_data['sa_file_name'],
        file_id=dev_data['csv_file_id'],
        out_path=download_dest_path,
    )
    csv_url = csv_public_url_get(f'dane-publiczne/{code}/{relative_ym_path}/{file_name}')

    # INFO: XML - Fill
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

    ET.indent(datasets, space='    ')
    validate_xml_against_schema(tree)

    tree.write(xml_public_path, encoding='utf-8', xml_declaration=True)

    # INFO: checksum
    checksum = file_md5_checksum(xml_public_path)
    checksum_filename = f'{code.upper()}.md5'
    checksum_public_path = BASE_PUBLIC_DATA_PATH / checksum_filename
    with open(checksum_public_path, 'w') as f:
        f.write(checksum)
    logger.info(f'finished processing: {developer_code}')
    return Status.PROCESSED


def main():
    if os.geteuid() == 0:
        raise ValueError('DONT RUN AS ROOT')
    logger.info('START')
    results = []
    for code in developer_list_get():
        logger.info(f'GENERATE: {code}')
        try:
            status = developer_data_generate(code)
            results.append(DeveloperResult(code=code, status=status))
        except Exception:
            error = traceback.format_exc()
            logger.error(f'FAILED: {code}\n{error}')
            results.append(
                DeveloperResult(code=code, status=Status.FAILED, error=error)
            )
    logger.info('FINISED')

    send_run_summary(results)

    if any(r.status is Status.FAILED for r in results):
        sys.exit(1)


if __name__ == '__main__':
    main()
