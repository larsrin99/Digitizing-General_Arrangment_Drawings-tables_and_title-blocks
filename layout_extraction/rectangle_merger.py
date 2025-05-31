# rectangle_merger.py

from shapely.geometry import box
from shapely.ops import unary_union
from lxml import etree
from typing import List, Dict, Any, Optional
from .data_structures import TextBox
from .utils import parse_bbox, bbox_area, bbox_is_contained, bbox_to_str
import logging

logger = logging.getLogger(__name__)

def parse_rectangles_xml(xml_path: str) -> List[Dict[str, Any]]:
    tree = etree.parse(xml_path)
    root = tree.getroot()

    rectangles = []
    for rect in root.findall("rectangle"):
        bbox = parse_bbox(rect.attrib.get("bbox"))
        if not bbox:
            continue

        texts = []
        for text in rect.findall("text"):
            tbbox = parse_bbox(text.attrib.get("bbox"))
            if not tbbox:
                logger.warning(f"Skipping invalid <text> bbox: {text.attrib.get('bbox')}")
                continue
            ttext = text.text.strip() if text.text else ""
            texts.append(TextBox(bbox=tbbox, text=ttext, page_number=-1))
        rectangles.append({
            "bbox": bbox,
            "texts": texts
        })
    return rectangles

def is_margin_label(rect: Dict[str, Any], page_height: float) -> bool:
    if not rect.get("texts"):
        return False

    x0, y0, x1, y1 = rect["bbox"]
    top_thresh = 0.05 * page_height
    bottom_thresh = 0.95 * page_height
    in_margin = y0 < top_thresh or y1 > bottom_thresh

    if not in_margin or len(rect["texts"]) < 1 or len(rect["texts"]) > 20:
        return False

    return all(t.text.strip().isdigit() for t in rect["texts"])

def merge_rectangles_distinct(rectangles: List[Dict[str, Any]], page_height: Optional[float] = None) -> List[Dict[str, Any]]:
    merged = []
    used = set()
    seen_texts = set()

    def rect_to_box(r):
        return box(*r["bbox"])

    def tb_to_tuple(tb: TextBox):
        return tuple(tb.bbox) + (tb.text,)

    def is_significantly_smaller(r1, r2):
        area1 = bbox_area(r1["bbox"])
        area2 = bbox_area(r2["bbox"])
        return area1 < area2 and (area1 / area2) < 0.98

    for i, rect1 in enumerate(rectangles):
        if i in used or (page_height and is_margin_label(rect1, page_height)):
            continue

        r1_box = rect_to_box(rect1)
        merged_rects = [rect1]
        merged_texts = set(tb_to_tuple(tb) for tb in rect1["texts"])
        shared_texts = set()

        for j in range(i + 1, len(rectangles)):
            if j in used:
                continue
            rect2 = rectangles[j]
            if page_height and is_margin_label(rect2, page_height):
                continue

            r2_box = rect_to_box(rect2)
            if r1_box.intersects(r2_box):
                if is_significantly_smaller(rect1, rect2):
                    continue

                tbs2 = set(tb_to_tuple(tb) for tb in rect2["texts"])
                for tb in rect2["texts"]:
                    coords = tb.bbox
                    try:
                        if r1_box.intersection(r2_box).contains(box(*coords)):
                            shared_texts.add(tb_to_tuple(tb))
                    except Exception as e:
                        logger.warning(f"⚠️ Skipping malformed textbox bbox {coords} — {e}")

                merged_rects.append(rect2)
                merged_texts.update(tbs2 - shared_texts)
                used.add(j)

        if all(tb[4].strip() in seen_texts for tb in merged_texts):
            used.add(i)
            continue

        for tb in merged_texts:
            seen_texts.add(tb[4].strip())

        union_box = unary_union([rect_to_box(r) for r in merged_rects])
        merged.append({
            "bbox": tuple(union_box.bounds),
            "texts": [TextBox(bbox=tb[:4], text=tb[4], page_number=-1) for tb in merged_texts]
        })

        if shared_texts:
            shared_box = unary_union([box(*tb[:4]) for tb in shared_texts])
            merged.append({
                "bbox": tuple(shared_box.bounds),
                "texts": [TextBox(bbox=tb[:4], text=tb[4], page_number=-1) for tb in shared_texts]
            })

        used.add(i)

    filtered = []
    for i, r1 in enumerate(merged):
        keep = True
        for j, r2 in enumerate(merged):
            if i != j and bbox_is_contained(r1["bbox"], r2["bbox"]):
                keep = False
                break
        if keep:
            filtered.append(r1)

    return filtered

def export_rectangles_to_xml(rectangles: List[Dict[str, Any]], output_path: str):
    root = etree.Element("rectangles")
    for rect in rectangles:
        rect_elem = etree.SubElement(root, "rectangle")
        rect_elem.set("bbox", bbox_to_str(rect["bbox"]))
        for tb in rect["texts"]:
            text_elem = etree.SubElement(rect_elem, "text")
            text_elem.set("bbox", bbox_to_str(tb.bbox))
            text_elem.text = tb.text
    tree = etree.ElementTree(root)
    tree.write(output_path, pretty_print=True, encoding="UTF-8", xml_declaration=True)
