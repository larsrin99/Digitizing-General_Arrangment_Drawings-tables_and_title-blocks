from lxml import etree
from collections import defaultdict
from semantic_annotation.bbox_utils import parse_bbox
import json
import re


class TitleBlockOrganizer:
    def __init__(self, xml_root):
        self.root = xml_root

    def detect_revision_table(self):
        for titleblock in self.root.findall(".//titleblock"):
            cells = titleblock.findall(".//cell")
            if not cells:
                continue

            min_x, max_x = 796.53, 1306.77
            min_y, max_y = 56.70, 255.12

            rev_cells = []
            for cell in cells:
                x0, y0, x1, y1 = parse_bbox(cell.attrib['bbox'])
                if min_x <= x0 and x1 <= max_x and min_y <= y0 and y1 <= max_y:
                    rev_cells.append(cell)

            if len(rev_cells) < 4:
                continue

            rows_by_y = defaultdict(list)
            for cell in rev_cells:
                _, y0, _, y1 = parse_bbox(cell.attrib['bbox'])
                y_center = round((y0 + y1) / 2.0, 1)
                rows_by_y[y_center].append(cell)

            sorted_ys = sorted(rows_by_y.keys(), reverse=True)
            sorted_rows = [sorted(rows_by_y[y], key=lambda c: parse_bbox(c.attrib['bbox'])[0]) for y in sorted_ys]

            rev_table_bbox = [min_x, min_y, max_x, max_y]
            rev_table = etree.Element("revision_table", bbox=','.join(map(str, rev_table_bbox)))
            for row_index, row in enumerate(sorted_rows):
                row_elem = etree.Element("row", id=f"rev_r{row_index+1}")
                for col_index, cell in enumerate(row):
                    col_elem = etree.Element("column", attrib=cell.attrib)
                    col_elem.set("id", f"rev_r{row_index+1}_c{col_index+1}")
                    for child in cell:
                        col_elem.append(child)
                    row_elem.append(col_elem)
                rev_table.append(row_elem)

            titleblock.append(rev_table)

            for cell in rev_cells:
                titleblock.remove(cell)

    def detect_titleblock_fields(self, json_config_path):
        with open(json_config_path, 'r') as f:
            config = json.load(f)

        label_tokens = set()
        for labels in config.values():
            for label in labels:
                for token in label.lower().strip().split():
                    label_tokens.add(token)

        for titleblock in self.root.findall(".//titleblock"):
            data_fields = etree.Element("document_metadata")
            titleblock.append(data_fields)

            cells = titleblock.findall(".//cell")
            used_cells = set()

            for cell in cells:
                bbox = cell.attrib['bbox']
                text_elems = cell.findall(".//text")
                texts = [t.text.strip() for t in text_elems if t.text and t.text.strip()]
                lowered = [t.lower() for t in texts]

                if len(texts) == 1:
                    if any(texts[0].lower() in [v.lower().strip() for v in labels] for labels in config.values()):
                        continue

                if len(texts) == 2:
                    if all(any(token in label_tokens for token in text.lower().split()) for text in texts):
                        continue
                    for field_id, label_variants in config.items():
                        for variant in label_variants:
                            variant = variant.lower().strip()
                            if variant in lowered[0]:
                                field_elem = etree.Element("document_property", id=field_id, bbox=bbox)
                                field_elem.text = texts[1]
                                data_fields.append(field_elem)
                                titleblock.remove(cell)
                                used_cells.add(cell)
                                break
                            elif variant in lowered[1]:
                                field_elem = etree.Element("document_property", id=field_id, bbox=bbox)
                                field_elem.text = texts[0]
                                data_fields.append(field_elem)
                                titleblock.remove(cell)
                                used_cells.add(cell)
                                break
                        else:
                            continue
                        break
                    continue

                flat_line = " ".join(lowered)
                for field_id, label_variants in config.items():
                    for variant in label_variants:
                        variant_tokens = variant.lower().strip().split()
                        variant_str = " ".join(variant_tokens)

                        matched_indices = []
                        for win_size in range(1, len(lowered) + 1):
                            for i in range(len(lowered) - win_size + 1):
                                if " ".join(lowered[i:i+win_size]) == variant_str:
                                    matched_indices = list(range(i, i+win_size))
                                    break
                            if matched_indices:
                                break

                        if not matched_indices:
                            continue

                        label_boxes = [parse_bbox(text_elems[i].attrib['bbox']) for i in matched_indices]
                        label_x0s = [b[0] for b in label_boxes]
                        label_y0s = [b[1] for b in label_boxes]
                        label_y1s = [b[3] for b in label_boxes]

                        label_x0 = min(label_x0s)
                        label_y_max = max(label_y1s)

                        value_candidates = []
                        for j, t in enumerate(texts):
                            if j in matched_indices:
                                continue
                            x0, y0, x1, y1 = parse_bbox(text_elems[j].attrib['bbox'])
                            value_candidates.append((y0, x0, t))

                        value_candidates.sort()
                        value = " ".join(v[2] for v in value_candidates).strip()

                        field_elem = etree.Element("document_property", id=field_id, bbox=bbox)
                        field_elem.text = value
                        data_fields.append(field_elem)
                        titleblock.remove(cell)
                        used_cells.add(cell)
                        break
                    else:
                        continue
                    break

            self.extract_vertical_label_value_pairs(titleblock, config, data_fields, used_cells)
            self.extract_horizontal_free_text_fields(titleblock, config, data_fields, used_cells)
            self.extract_final_missing_fields(titleblock, config, data_fields, used_cells)


    def extract_vertical_label_value_pairs(self, titleblock, config, data_fields, used_cells):
        cells = [cell for cell in titleblock.findall(".//cell") if cell not in used_cells]
        cell_map = {}
        for cell in cells:
            x0, y0, x1, y1 = parse_bbox(cell.attrib['bbox'])
            center_x = round((x0 + x1) / 2.0, 1)
            center_y = round((y0 + y1) / 2.0, 1)
            cell_map[(center_x, center_y)] = cell

        for label_cell in cells:
            label_texts = [t.text.strip().lower() for t in label_cell.findall(".//text") if t.text and t.text.strip()]
            if not label_texts:
                continue

            label_flat = " ".join(label_texts)
            for field_id, variants in config.items():
                if any(v.lower() in label_flat for v in variants):
                    x0, y0, x1, y1 = parse_bbox(label_cell.attrib['bbox'])
                    center_x = round((x0 + x1) / 2.0, 1)
                    center_y = round((y0 + y1) / 2.0, 1)

                    for (cx, cy), value_cell in cell_map.items():
                        y_diff = cy - center_y
                        if cx == center_x and 15.0 <= abs(y_diff) <= 30.0:
                            value_texts = [t.text.strip() for t in value_cell.findall(".//text") if t.text and t.text.strip()]
                            if not value_texts:
                                continue

                            if field_id in ["size", "scale"]:
                                size_val, scale_val = None, None
                                for vt in value_texts:
                                    if not size_val and re.match(r"^[A-Z]\d?$", vt):
                                        size_val = vt
                                    elif not scale_val and re.match(r"^\d+\s*:\s*\d+$", vt):
                                        scale_val = vt

                                if size_val:
                                    field_elem = etree.Element("document_property", id="size", bbox=value_cell.attrib['bbox'])
                                    field_elem.text = size_val
                                    data_fields.append(field_elem)
                                if scale_val:
                                    field_elem = etree.Element("document_property", id="scale", bbox=value_cell.attrib['bbox'])
                                    field_elem.text = scale_val
                                    data_fields.append(field_elem)
                            else:
                                field_elem = etree.Element("document_property", id=field_id, bbox=value_cell.attrib['bbox'])
                                field_elem.text = " ".join(value_texts)
                                data_fields.append(field_elem)

                            if value_cell in titleblock:
                                titleblock.remove(value_cell)
                            used_cells.add(value_cell)

                    if label_cell in titleblock:
                        titleblock.remove(label_cell)
                    used_cells.add(label_cell)
                    break

    def extract_horizontal_free_text_fields(self, titleblock, config, data_fields, used_cells):
        all_texts = [t for t in titleblock.findall(".//text") if t.getparent().tag != "document_property"]
        label_map = {}
        for t in all_texts:
            text_str = t.text.strip().lower() if t.text else ""
            for field_id, variants in config.items():
                if any(text_str == v.strip().lower() or text_str.rstrip(':') == v.strip().lower().rstrip(':') for v in variants):
                    label_map.setdefault(field_id, []).append(t)

        for field_id, label_texts in label_map.items():
            for label in label_texts:
                x0_l, y0_l, x1_l, y1_l = parse_bbox(label.attrib['bbox'])
                cx_l = (x0_l + x1_l) / 2
                cy_l = (y0_l + y1_l) / 2

                best_match = None
                best_dist = float('inf')

                for cell in titleblock.findall(".//cell"):
                    if cell in used_cells:
                        continue
                    x0_c, y0_c, x1_c, y1_c = parse_bbox(cell.attrib['bbox'])
                    cx_c = (x0_c + x1_c) / 2
                    cy_c = (y0_c + y1_c) / 2

                    if abs(cx_c - cx_l) < 5 and y0_c > y1_l and y0_c - y1_l < 50:
                        dist = y0_c - y1_l
                        if dist < best_dist:
                            best_match = cell
                            best_dist = dist

                if best_match is not None:
                    texts = [t.text.strip() for t in best_match.findall(".//text") if t.text and t.text.strip()]
                    if texts:
                        field_elem = etree.Element("document_property", id=field_id, bbox=best_match.attrib['bbox'])
                        field_elem.text = " ".join(texts)
                        data_fields.append(field_elem)
                        used_cells.add(best_match)
                        if best_match in titleblock:
                            titleblock.remove(best_match)
                if label.getparent() is titleblock:
                    titleblock.remove(label)

    def extract_final_missing_fields(self, titleblock, config, data_fields, used_cells):
            label_lines = defaultdict(list)
            for t in titleblock.findall(".//text"):
                y0 = round(parse_bbox(t.attrib['bbox'])[1], 1)
                label_lines[y0].append(t)

            for y in sorted(label_lines.keys(), reverse=True):
                line = sorted(label_lines[y], key=lambda t: parse_bbox(t.attrib['bbox'])[0])
                label_text = " ".join(t.text.strip() for t in line if t.text).lower()
                for field_id, variants in config.items():
                    for variant in variants:
                        if variant.lower().strip() in label_text:
                            label_bbox = [parse_bbox(t.attrib['bbox']) for t in line]
                            min_x = min(b[0] for b in label_bbox)
                            max_x = max(b[2] for b in label_bbox)
                            min_y = min(b[1] for b in label_bbox)
                            max_y = max(b[3] for b in label_bbox)

                            for cell in titleblock.findall(".//cell"):
                                if cell in used_cells:
                                    continue
                                cx0, cy0, cx1, cy1 = parse_bbox(cell.attrib['bbox'])
                                if (min_x - 10 <= cx0 <= max_x + 10) and (cy1 <= min_y):
                                    texts = [t.text.strip() for t in cell.findall(".//text") if t.text and t.text.strip()]
                                    if not texts:
                                        continue
                                    field_elem = etree.Element("document_property", id=field_id)
                                    field_elem.text = " ".join(texts)
                                    field_elem.set("bbox", cell.attrib['bbox'])
                                    data_fields.append(field_elem)
                                    used_cells.add(cell)
                                    for t in line:
                                        if t in titleblock:
                                            titleblock.remove(t)
                                    break