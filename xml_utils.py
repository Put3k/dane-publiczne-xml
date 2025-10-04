import requests
import xml.etree.ElementTree as ET
from lxml import etree
from dataclasses import dataclass, field
from typing import List

# ======= MODELE =======

DEWELOPER_NAZWA = 'Arcus Development Sp. z o.o.'

@dataclass
class Resource:
    # Dynamic
    extIdent: str
    url: str
    dataDate: str

    # Constant
    status: str = 'published'
    title_pl: str = 'Ceny ofertowe mieszkań dewelopera {developer} w {year} r.'
    title_en: str = "Offer prices of apartments of developer {developer} in {year}."
    description_pl: str = (
        'Zbiór danych zawiera informacje o cenach ofertowych mieszkań '
        'dewelopera {developer} udostępniane zgodnie z art. 19b. ust. 1 Ustawy '
        'z dnia 20 maja 2021 r. o ochronie praw nabywcy lokalu mieszkalnego '
        'lub domu jednorodzinnego oraz Deweloperskim Funduszu Gwarancyjnym '
        '(Dz. U. z 2024 r. poz. 695).'
    )
    description_en: str = (
        'The dataset contains information on offer prices of apartments of the '
        'developer {developer} made available in accordance with art. 19b. ust. 1 '
        'Ustawy z dnia 20 maja 2021 r. o ochronie praw nabywcy lokalu '
        'mieszkalnego lub domu jednorodzinnego oraz Deweloperskim Funduszu '
        'Gwarancyjnym (Dz. U. z 2024 r. poz. 695).'
    )
    availability: str = 'local'
    specialSigns: List[str] = field(default_factory=lambda: ['X'])
    hasDynamicData: bool = False
    hasHighValueData: bool = True
    hasHighValueDataFromEuropeanCommissionList: bool = False
    hasResearchData: bool = False
    containsProtectedData: bool = False

@dataclass
class Dataset:
    # Constants
    status: str = 'published'
    extIdent: str = 'ARCUS2025'
    title_pl: str = 'Ceny ofertowe mieszkań dewelopera {developer} w {year} r.'
    title_en: str = "Offer prices of apartments of developer {developer} in {year}."
    description_pl: str = (
        'Zbiór danych zawiera informacje o cenach ofertowych mieszkań '
        'dewelopera {developer} udostępniane zgodnie z art. 19b. ust. 1 Ustawy '
        'z dnia 20 maja 2021 r. o ochronie praw nabywcy lokalu mieszkalnego '
        'lub domu jednorodzinnego oraz Deweloperskim Funduszu Gwarancyjnym '
        '(Dz. U. z 2024 r. poz. 695).'
    )
    description_en: str = (
        'The dataset contains information on offer prices of apartments of the '
        'developer {developer} made available in accordance with art. 19b. ust. 1 '
        'Ustawy z dnia 20 maja 2021 r. o ochronie praw nabywcy lokalu '
        'mieszkalnego lub domu jednorodzinnego oraz Deweloperskim Funduszu '
        'Gwarancyjnym (Dz. U. z 2024 r. poz. 695).'
    )
    updateFrequency: str = 'daily'
    hasDynamicData: bool = False
    hasHighValueData: bool = True
    hasHighValueDataFromEuropeanCommissionList: bool = False
    hasResearchData: bool = False
    categories: List[str] = field(default_factory=lambda: ['ECON'])
    tags: List[str] = field(default_factory=lambda: ['Deweloper'])

    # Loaded from file
    resources: List[Resource] = field(default_factory=list)


def load_xsd(xsd_url: str) -> etree.XMLSchema:
    """
    Pobiera schemat XSD z URL i zwraca obiekt XMLSchema.
    (Możesz też zamiast URL podać lokalną ścieżkę do pliku .xsd.)
    """
    resp = requests.get(xsd_url)
    resp.raise_for_status()
    xsd_doc = etree.XML(resp.content)
    schema = etree.XMLSchema(xsd_doc)
    return schema


def validate_xml_against_schema(xml_filepath: str, schema: etree.XMLSchema) -> bool:
    """
    Waliduje plik XML względem podanego schematu.
    Zwraca True, jeśli walidacja przeszła, inaczej podnosi wyjątek z informacją.
    """
    parser = etree.XMLParser(ns_clean=True)
    xml_doc = etree.parse(xml_filepath, parser)
    valid = schema.validate(xml_doc)
    if not valid:
        # zbierz błędy
        errors = []
        for error in schema.error_log:
            errors.append(f'Line {error.line}, Column {error.column}: {error.message}')
        err_msg = 'XML nie przeszedł walidacji XSD:\n' + '\n'.join(errors)
        raise ValueError(err_msg)
    return True


def parse_resources(filepath: str) -> List[Resource]:
    tree = ET.parse(filepath)
    root = tree.getroot()

    resources: List[Resource] = []
    for res in root.findall('.//resource'):
        r = Resource(
            status=res.attrib.get('status', ''),
            extIdent=res.findtext('extIdent', ''),
            url=res.findtext('url', ''),
            title_pl=res.findtext('title/polish', ''),
            title_en=res.findtext('title/english', ''),
            description_pl=res.findtext('description/polish', ''),
            description_en=res.findtext('description/english', ''),
            availability=res.findtext('availability', ''),
            dataDate=res.findtext('dataDate', ''),
            specialSigns=[s.text for s in res.findall('specialSigns/specialSign') if s.text],
            hasDynamicData=(res.findtext('hasDynamicData', 'false') == 'true'),
            hasHighValueData=(res.findtext('hasHighValueData', 'false') == 'true'),
            hasHighValueDataFromEuropeanCommissionList=(
                res.findtext('hasHighValueDataFromEuropeanCommissionList', 'false') == 'true'
            ),
            hasResearchData=(res.findtext('hasResearchData', 'false') == 'true'),
            containsProtectedData=(res.findtext('containsProtectedData', 'false') == 'true'),
        )
        resources.append(r)
    return resources

def add_new_resource(dataset: Dataset, new_res: Resource) -> None:
    dataset.resources.append(new_res)

def create_dataset_with_resources(xml_filepath: str, xsd_url: str) -> Dataset:
    # Validate XML with XSD
    schema = load_xsd(xsd_url)
    validate_xml_against_schema(xml_filepath, schema)

    ds = Dataset()
    ds.resources = parse_resources(xml_filepath)
    return ds


if __name__ == '__main__':
    filepath = 'Przykład_3_kolejne_publikacje_v.1.13_21.08.2025.xml'
    resources = parse_resources(filepath)

    # Utworzenie datasetu ze stałymi polami
    ds = Dataset()

    # Doładowanie zasobów z pliku
    ds.resources = parse_resources(filepath)

    # Dodanie nowego zasobu ręcznie
    new_resource = Resource(
        status='published',
        extIdent='TEST2137',
        url='https://strona-dewelopera.com.pl/Ceny-ofertowe-mieszkan-dewelopera-TESTY-2025-09-28.csv',
        title_pl='Ceny ofertowe mieszkań dewelopera TESTY 2025-09-28',
        title_en="Offer prices for developer's apartments TESTY 2025-09-28",
        description_pl='Dane dotyczące cen ofertowych mieszkań TESTY z dnia 2025-09-28.',
        description_en='Data on offer prices of apartments TESTY as of 2025-09-28.',
        availability='local',
        dataDate='2025-09-28',
        specialSigns=['X'],
        hasDynamicData=False,
        hasHighValueData=True,
        hasHighValueDataFromEuropeanCommissionList=False,
        hasResearchData=False,
        containsProtectedData=False,
    )
    add_new_resource(ds, new_resource)

    # Podgląd wyników
    print(f'Dataset: {ds.title_pl} ({ds.extIdent})')
    for r in ds.resources:
        print(f'  - [{r.status}] {r.dataDate}: {r.url} - {r.extIdent} - {r.title_pl}')


    xsd_url = 'https://www.dane.gov.pl/static/xml/otwarte_dane_latest.xsd'
    try:
        ds = create_dataset_with_resources(filepath, xsd_url)
        print('Walidacja powiodła się, dataset utworzony.')
        print(f'Dataset ma {len(ds.resources)} zasobów.')
    except Exception as e:
        print('Błąd:', str(e))
