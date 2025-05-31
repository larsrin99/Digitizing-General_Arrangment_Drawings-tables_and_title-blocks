# textbox_mapper.py

import logging
from lxml import etree
from typing import List, Tuple, Union
from .data_structures import TextBox
from .utils import parse_bbox, bbox_center, bbox_contains_point, bbox_to_str

logger = logging.getLogger(__name__)

BBox = Tuple[float, float, float, float]

class TextboxMapper:
    def __init__(self, rectangles: List[dict], textbox_elements: List[etree._Element]):
        self.rectangles = rectangles
        self.textbox_elements = [
            tb for tb in textbox_elements
            if "".join(text.text or "" for text in tb.xpath(".//text")).strip()
        ]

    def _get_bbox(self, val: Union[str, BBox]) -> BBox:
        return parse_bbox(val) if isinstance(val, str) else val

    def map_textboxes(self) -> List[dict]:
        mapped = []
        for rect in self.rectangles:
            bbox = self._get_bbox(rect["bbox"])
            rect["bbox"] = bbox
            rect["area"] = self.compute_area(bbox)
            rect["texts"] = []
            rect["textbox_elements"] = []

        for textbox_el in self.textbox_elements:
            tbbox_str = textbox_el.attrib.get("bbox")
            if not tbbox_str:
                continue
            tbbox = parse_bbox(tbbox_str)
            cx, cy = bbox_center(tbbox)

            for rect in self.rectangles:
                if bbox_contains_point(rect["bbox"], cx, cy):
                    content = " ".join(
                        "".join(text.text or "" for text in line.xpath(".//text"))
                        for line in textbox_el.xpath(".//textline")
                    ).strip()
                    if content:
                        textbox = TextBox(bbox=tbbox, text=content, page_number=-1)
                        rect["texts"].append(textbox)
                        rect["textbox_elements"].append(textbox_el)

        for rect in self.rectangles:
            if rect["texts"]:
                mapped.append(rect)

        return mapped

    def compute_area(self, bbox: BBox) -> float:
        x0, y0, x1, y1 = bbox
        return abs((x1 - x0) * (y1 - y0))

    def export_to_xml(self, mapped_rects: List[dict], output_path: str):
        root = etree.Element("rectangles")
        for rect in mapped_rects:
            rect_el = etree.SubElement(root, "rectangle", bbox=bbox_to_str(rect["bbox"]))
            for tb in rect["texts"]:
                etree.SubElement(rect_el, "text", bbox=bbox_to_str(tb.bbox)).text = tb.text
        tree = etree.ElementTree(root)
        tree.write(output_path, pretty_print=True, xml_declaration=True, encoding="utf-8")
        logger.info(f"✅ Saved mapped rectangles to {output_path}")
