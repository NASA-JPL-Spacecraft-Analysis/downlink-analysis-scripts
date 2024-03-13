from typing import List
from io import TextIOWrapper
from xml.etree import ElementTree

from fspa_scripts.ctu_merlin.data.javadocs import JavadocState


def parse_javadoc_xml(fid: TextIOWrapper) -> List[JavadocState]:
    etree = ElementTree.parse(fid)
    states = []
    for state_el in etree.findall('ENTRY'):

        resource_el = state_el.find('resource')
        resource = resource_el.text.strip() if resource_el is not None else None

        units_el = state_el.find('units')
        units = units_el.text.strip() if units_el is not None else None

        docs_el = state_el.find('docs')
        docs = ' '.join([
            l.strip()for l in docs_el.text.split("\n")
        ]).strip() if docs_el is not None else None

        states.append(JavadocState(resource, units, docs))

    return states
