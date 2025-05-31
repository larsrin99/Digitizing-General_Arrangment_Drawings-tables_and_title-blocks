# pipeline/intersection_loader.py
from lxml import etree

class IntersectionLoader:
    def __init__(self, xml_path):
        self.xml_path = xml_path

    def load(self):
        tree = etree.parse(self.xml_path)
        root = tree.getroot()
        return [
            (float(pt.attrib["x"]), float(pt.attrib["y"]))
            for pt in root.findall(".//point")
        ]