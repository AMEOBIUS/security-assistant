# VULNERABLE:
# import xml.etree.ElementTree as ET
# tree = ET.fromstring(xml_data)  # Vulnerable to XXE depending on python version/lib

# SECURE (using defusedxml):
import defusedxml.ElementTree as ET

# defusedxml will raise an error if entities are present
tree = ET.fromstring(xml_data)

# SECURE (lxml - disable DTD/Entities):
from lxml import etree

parser = etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    dtd_validation=False,
    load_dtd=False
)
tree = etree.fromstring(xml_data, parser=parser)
