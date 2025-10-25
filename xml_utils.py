import requests
from lxml import etree as ET
from dataclasses import dataclass, field
from typing import List


@dataclass
class Resource:
    # Dynamic
    extIdent: str
    url: str
    dataDate: str

    # Constant
    status: str = 'published'
    title_pl: str = 'Ceny ofertowe mieszkań dewelopera {developer_name} w {year} r.'
    title_en: str = "Offer prices of apartments of developer {developer_name} in {year}."
    description_pl: str = (
        'Zbiór danych zawiera informacje o cenach ofertowych mieszkań '
        'dewelopera {developer_name} udostępniane zgodnie z art. 19b. ust. 1 Ustawy '
        'z dnia 20 maja 2021 r. o ochronie praw nabywcy lokalu mieszkalnego '
        'lub domu jednorodzinnego oraz Deweloperskim Funduszu Gwarancyjnym '
        '(Dz. U. z 2024 r. poz. 695).'
    )
    description_en: str = (
        'The dataset contains information on offer prices of apartments of the '
        'developer {developer_name} made available in accordance with art. 19b. ust. 1 '
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

    def to_etree_element(self):
        res_el = ET.Element('resource', attrib={'status': self.status})
        ET.SubElement(res_el, 'extIdent').text = self.extIdent
        ET.SubElement(res_el, 'url').text = self.url

        res_title_el = ET.SubElement(res_el, 'title')
        ET.SubElement(res_title_el, 'polish').text = self.title_pl
        ET.SubElement(res_title_el, 'english').text = self.title_en

        res_desc_el = ET.SubElement(res_el, 'description')
        ET.SubElement(res_desc_el, 'polish').text = self.description_pl
        ET.SubElement(res_desc_el, 'english').text = self.description_en

        ET.SubElement(res_el, 'availability').text = self.availability
        ET.SubElement(res_el, 'dataDate').text = self.dataDate

        special_el = ET.SubElement(res_el, 'specialSigns')
        for s in self.specialSigns:
            ET.SubElement(special_el, 'specialSign').text = s

        ET.SubElement(res_el, 'hasDynamicData').text = str(
            self.hasDynamicData
        ).lower()
        ET.SubElement(res_el, 'hasHighValueData').text = str(
            self.hasHighValueData
        ).lower()
        ET.SubElement(
            res_el, 'hasHighValueDataFromEuropeanCommissionList'
        ).text = str(self.hasHighValueDataFromEuropeanCommissionList).lower()
        ET.SubElement(res_el, 'hasResearchData').text = str(
            self.hasResearchData
        ).lower()
        ET.SubElement(res_el, 'containsProtectedData').text = str(
            self.containsProtectedData
        ).lower()
        return res_el


def resource_exists(resources: ET.Element, identifier: str):
    for res in resources.findall('resource'):
        ext_ident = res.find('extIdent').text
        if ext_ident == identifier:
            return True
    return False


def load_xsd(xsd_url: str) -> ET.XMLSchema:
    resp = requests.get(xsd_url)
    resp.raise_for_status()
    xsd_doc = ET.XML(resp.content)
    schema = ET.XMLSchema(xsd_doc)
    return schema


def validate_xml_against_schema(xml_doc) -> bool:
    schema = load_xsd('https://www.dane.gov.pl/static/xml/otwarte_dane_latest.xsd')
    valid = schema.validate(xml_doc)
    if not valid:
        errors = []
        for error in schema.error_log:
            errors.append(f'Line {error.line}, Column {error.column}: {error.message}')
        err_msg = 'XML nie przeszedł walidacji XSD:\n' + '\n'.join(errors)
        raise ValueError(err_msg)
    return True


if __name__ == '__main__':
    in_file = 'Przykład_3_kolejne_publikacje_v.1.13_21.08.2025.xml'

    # TREE
    tree = ET.parse(in_file)
    root = tree.getroot()

    resources = root.find('.//resources')
    if resources is None:
        msg = 'No resources in ElementTree'
        raise ValueError(msg)

    new_resource = Resource(
        status='published',
        extIdent='PAPAJ',
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
    resource_element = new_resource.to_etree_element()

    resources.append(resource_element)

    ET.indent(root, space='    ')
    validate_xml_against_schema(tree)

    output_path = '/home/kacper/projects/dane-publiczne/output.xml'
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
