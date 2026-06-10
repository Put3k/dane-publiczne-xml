#!/usr/bin/env python3
'''
_fill_the_gap.py

Backfill missing daily resources in a developer's published XML by copying the
nearest *later* day's already-published CSV (the "day after"). The daily run
publishes one resource per developer per day keyed by ISO date; a failed day
leaves an interior gap that this script fills on demand.

Drive only ever holds the current day's prices, so a past day can only be
reconstructed from a neighbour's CSV already on disk.

Usage:
    python _fill_the_gap.py <DEVELOPER_CODE> <DATE_FROM> <DATE_TO>

    DATE_FROM / DATE_TO are inclusive, ISO YYYY-MM-DD, same year.

See memory/fill-the-gap-plan.md for the full design.
'''

import sys
import shutil
import logging
import argparse
from datetime import date, timedelta
from logging.handlers import RotatingFileHandler

from lxml import etree as ET

from settings import BASE_DIR, BASE_PUBLIC_DATA_PATH
from dane_publiczne import (
    csv_public_url_get,
    file_md5_checksum,
    developer_data_get,
)
from xml_utils import (
    Resource,
    Dataset,
    dataset_find,
    validate_xml_against_schema,
)


# logging - own file, kept separate from the daily run's log
log_handler = RotatingFileHandler(
    filename=BASE_DIR / 'cache/fill-the-gap.log',
    mode='a',
    maxBytes=5 * 1024 * 1024,
    backupCount=4,
    encoding='utf-8',
)
log_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
)
logger = logging.getLogger('fill_the_gap')
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
logger.propagate = False


def find_gaps(existing_dates, date_from, date_to):
    '''Pure: return ordered [(gap, source)] for every missing day in
    [date_from, date_to]. `source` is the nearest later day that has data and
    is <= date_to. Days with no in-window successor are omitted (unfillable).'''
    existing = set(existing_dates)
    one = timedelta(days=1)
    gaps = []
    day = date_from
    while day <= date_to:
        if day not in existing:
            source = None
            probe = day + one
            while probe <= date_to:
                if probe in existing:
                    source = probe
                    break
                probe += one
            if source is not None:
                gaps.append((day, source))
        day += one
    return gaps


def existing_resource_dates(resources):
    '''ISO-date extIdents present under a dataset's <resources>.'''
    dates = set()
    for res in resources.findall('resource'):
        ext = res.find('extIdent')
        if ext is None or not ext.text:
            continue
        try:
            dates.add(date.fromisoformat(ext.text.strip()))
        except ValueError:
            continue  # non-date extIdent
    return dates


def resource_find(resources, identifier):
    for res in resources.findall('resource'):
        ext = res.find('extIdent')
        if ext is not None and ext.text == identifier:
            return res
    return None


def url_to_local_path(url):
    '''Map a public resource URL back to its file on disk. The host serves
    BASE_PUBLIC_DATA_PATH at /dane-publiczne/.'''
    marker = '/dane-publiczne/'
    idx = url.find(marker)
    if idx == -1:
        raise ValueError(f'unexpected resource url (no {marker!r}): {url}')
    relative = url[idx + len(marker):]
    return BASE_PUBLIC_DATA_PATH / relative


def build_resource(code, gap_date, dev_data):
    '''Build the backfilled Resource for `gap_date` (mirrors
    dane_publiczne.developer_data_generate's resource construction).'''
    iso = gap_date.isoformat()
    relative_ym = gap_date.strftime('%Y/%m')
    file_name = f'{gap_date.day}.csv'
    csv_url = csv_public_url_get(
        f'dane-publiczne/{code}/{relative_ym}/{file_name}'
    )
    name = dev_data['name']
    return Resource(
        status='published',
        extIdent=iso,
        url=csv_url,
        title_pl=f'Ceny ofertowe mieszkań dewelopera {name} {iso}',
        title_en=f"Offer prices for developer's apartments {name} {iso}",
        description_pl=f'Dane dotyczące cen ofertowych mieszkań {name} z dnia {iso}.',
        description_en=f'Data on offer prices of apartments {name} as of {iso}.',
        availability='local',
        dataDate=iso,
        specialSigns=['X'],
        hasDynamicData=False,
        hasHighValueData=True,
        hasHighValueDataFromEuropeanCommissionList=False,
        hasResearchData=False,
        containsProtectedData=False,
    )


def fill_gap(code, gap_date, source_date, resources, dev_data):
    '''Copy the source day's CSV to the gap day's own path and append the
    backfilled resource. Returns True on success, False if skipped because the
    source file is missing on disk.'''
    source_res = resource_find(resources, source_date.isoformat())
    source_path = url_to_local_path(source_res.find('url').text)
    if not source_path.is_file():
        logger.error(
            f'skip {gap_date} <- {source_date}: source file missing: {source_path}'
        )
        return False

    dest_dir = BASE_PUBLIC_DATA_PATH / code / gap_date.strftime('%Y/%m')
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f'{gap_date.day}.csv'
    shutil.copyfile(source_path, dest_path)

    resources.append(build_resource(code, gap_date, dev_data).to_etree_element())
    logger.info(f'filled {gap_date} <- {source_date} (copied {source_path.name})')
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Backfill missing daily resources from the nearest later day.'
    )
    parser.add_argument('developer_code', type=str, help='developer code')
    parser.add_argument(
        'date_from', type=date.fromisoformat, help='inclusive, ISO YYYY-MM-DD'
    )
    parser.add_argument(
        'date_to', type=date.fromisoformat, help='inclusive, ISO YYYY-MM-DD'
    )
    args = parser.parse_args()

    code = args.developer_code.lower()
    date_from, date_to = args.date_from, args.date_to

    if date_from > date_to:
        parser.error('date_from must be <= date_to')
    if date_from.year != date_to.year:
        parser.error('date_from and date_to must be in the same year')

    dev_data = developer_data_get(code)

    xml_path = BASE_PUBLIC_DATA_PATH / f'{code.upper()}.xml'
    if not xml_path.is_file():
        sys.exit(f'XML not found: {xml_path}')
    tree = ET.parse(xml_path)
    datasets = tree.getroot()

    dataset_identifier = Dataset.ext_ident.format(
        developer_code=code.upper(), year=date_from.year
    )
    dataset = dataset_find(datasets, dataset_identifier)
    if dataset is None:
        sys.exit(f'Dataset not found: {dataset_identifier}')
    resources = dataset.find('./resources')
    if resources is None:
        sys.exit(f'No <resources> in dataset {dataset_identifier}')

    gaps = find_gaps(existing_resource_dates(resources), date_from, date_to)
    if not gaps:
        logger.info(f'{code.upper()} {date_from}..{date_to}: no fillable gaps')
        print('No fillable gaps in range.')
        return

    print(f'Gaps to fill for {code.upper()} ({date_from}..{date_to}):')
    for gap, source in gaps:
        print(f'  {gap} <- {source}')
    if input(f'Fill {len(gaps)} gap(s)? Y/N ') != 'Y':
        print('Aborted.')
        return

    filled, skipped = [], []
    for gap, source in gaps:
        if fill_gap(code, gap, source, resources, dev_data):
            filled.append((gap, source))
        else:
            skipped.append((gap, source))

    if filled:
        ET.indent(datasets, space='    ')
        validate_xml_against_schema(tree)
        tree.write(xml_path, encoding='utf-8', xml_declaration=True)

        checksum_path = BASE_PUBLIC_DATA_PATH / f'{code.upper()}.md5'
        with open(checksum_path, 'w') as f:
            f.write(file_md5_checksum(xml_path))

    summary = (
        f'{code.upper()} {date_from}..{date_to}: '
        f'{len(filled)} filled, {len(skipped)} skipped'
    )
    logger.info(summary)
    print(summary)
    for gap, source in filled:
        print(f'  filled  {gap} <- {source}')
    for gap, source in skipped:
        print(f'  skipped {gap} <- {source} (source file missing)')


if __name__ == '__main__':
    main()
