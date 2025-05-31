from lxml import etree
from semantic_annotation.bbox_utils import parse_bbox
from collections import defaultdict


def overlaps_margin_lines(rect_bbox_str, bottom_bbox, right_bbox):
    rx0, ry0, rx1, ry1 = parse_bbox(rect_bbox_str)
    bx0, by0, bx1, by1 = bottom_bbox
    rx0_, ry0_, rx1_, ry1_ = right_bbox

    overlaps_bottom = (ry1 >= by0 and ry0 <= by1)
    overlaps_right = (rx1 >= rx0_ and rx0 <= rx1_)

    return overlaps_bottom and overlaps_right


class TableStructurer:
    def __init__(self, rect_root, bottom_line_bbox, right_line_bbox):
        self.rect_root = rect_root
        self.bottom_line_bbox = bottom_line_bbox
        self.right_line_bbox = right_line_bbox

    def apply(self):
        self.rect_root.tag = "document"
        table_id = 0
        for rect in list(self.rect_root.findall(".//rectangle")):
            bbox_str = rect.attrib["bbox"]

            if overlaps_margin_lines(bbox_str, self.bottom_line_bbox, self.right_line_bbox):
                new_tag = "titleblock"
            else:
                cell_elems = rect.findall(".//cell")
                if len(cell_elems) < 2:
                    rect.getparent().remove(rect)
                    continue
                new_tag = "table"

            new_attrib = dict(rect.attrib)
            if new_tag == "table":
                new_attrib["id"] = f"t{table_id}"
                table_id += 1

            new_elem = etree.Element(new_tag, attrib=new_attrib)
            for child in rect:
                if child.tag != "intersection":
                    new_elem.append(child)

            if new_tag == "table":
                self._structure_rows(new_elem, new_attrib["id"])

            parent = rect.getparent()
            parent.replace(rect, new_elem)
        
        self._group_tables()

    def _group_tables(self):
        tables = self.rect_root.findall("table")
        if not tables:
            return

        tabular_section = etree.Element("tabular_section")
        for table in tables:
            self.rect_root.remove(table)
            tabular_section.append(table)

        self.rect_root.append(tabular_section)


    def _structure_rows(self, table_elem, table_id):
        rows_by_y = defaultdict(list)
        for cell in table_elem.findall(".//cell"):
            bbox = parse_bbox(cell.attrib["bbox"])
            y_top = round(bbox[1], 1)
            rows_by_y[y_top].append(cell)

        for cell in table_elem.findall(".//cell"):
            table_elem.remove(cell)

        sorted_ys = sorted(rows_by_y.keys(), reverse=True)
        sorted_rows = [(y, rows_by_y[y]) for y in sorted_ys]

        for row_index, (y, cells) in enumerate(sorted_rows):
            row_elem = etree.Element("row", attrib={"id": f"{table_id}_r{row_index}"})
            row_cells = sorted(cells, key=lambda c: parse_bbox(c.attrib["bbox"])[0])
            for col_index, cell in enumerate(row_cells):
                cell.tag = "column"
                cell.attrib["id"] = f"{table_id}_r{row_index}_c{col_index}"
                row_elem.append(cell)
            table_elem.append(row_elem)

        self._extract_header(table_elem)

    def _extract_header(self, table_elem):
        cell_y_mins = [
            parse_bbox(col.attrib["bbox"])[1]
            for row in table_elem.findall(".//row")
            for col in row.findall(".//column")
        ]
        if not cell_y_mins:
            return
        min_row_y = min(cell_y_mins)

        unassigned_texts = table_elem.findall("text")
        header_candidates = [
            (parse_bbox(t.attrib["bbox"])[0], t)
            for t in unassigned_texts
            if parse_bbox(t.attrib["bbox"])[3] > min_row_y
        ]

        if not header_candidates:
            return

        header_candidates.sort(key=lambda x: x[0])
        header_texts = [t.text.strip() for _, t in header_candidates if t.text]

        if not header_texts:
            return

        header_str = " ".join(header_texts)
        min_x = min(parse_bbox(t.attrib["bbox"])[0] for _, t in header_candidates)
        min_y = min(parse_bbox(t.attrib["bbox"])[1] for _, t in header_candidates)
        max_x = max(parse_bbox(t.attrib["bbox"])[2] for _, t in header_candidates)
        max_y = max(parse_bbox(t.attrib["bbox"])[3] for _, t in header_candidates)

        header_elem = etree.Element("header", attrib={
            "bbox": f"{min_x},{min_y},{max_x},{max_y}"
        })
        header_elem.text = header_str

        table_elem.insert(0, header_elem)
        for _, t in header_candidates:
            table_elem.remove(t)


def merge_column_texts(root):
    for col in root.iter("column"):
        text_nodes = col.findall("text")
        if len(text_nodes) <= 1:
            continue

        # Combine text content
        merged_text = " ".join(t.text.strip() for t in text_nodes if t.text and t.text.strip())

        # Combine bounding boxes
        bboxes = [parse_bbox(t.attrib["bbox"]) for t in text_nodes]
        x0 = min(b[0] for b in bboxes)
        y0 = min(b[1] for b in bboxes)
        x1 = max(b[2] for b in bboxes)
        y1 = max(b[3] for b in bboxes)

        # Remove old text nodes
        for t in text_nodes:
            col.remove(t)

        # Insert new merged text
        merged_elem = etree.Element("text", bbox=f"{x0},{y0},{x1},{y1}")
        merged_elem.text = merged_text
        col.append(merged_elem)

def merge_cell_texts_by_y0(root, y_tol=0.5):
    from collections import defaultdict

    for cell in root.iter("cell"):
        texts = cell.findall("text")
        if len(texts) <= 1:
            continue

        groups = defaultdict(list)
        for t in texts:
            y0 = round(parse_bbox(t.attrib["bbox"])[1] / y_tol) * y_tol
            groups[y0].append(t)

        if len(groups) == len(texts):
            continue  # nothing to merge

        # Clear existing texts
        for t in texts:
            cell.remove(t)

        for group in groups.values():
            merged_text = " ".join(t.text.strip() for t in group if t.text and t.text.strip())
            bboxes = [parse_bbox(t.attrib["bbox"]) for t in group]
            x0 = min(b[0] for b in bboxes)
            y0 = min(b[1] for b in bboxes)
            x1 = max(b[2] for b in bboxes)
            y1 = max(b[3] for b in bboxes)

            new_t = etree.Element("text", bbox=f"{x0},{y0},{x1},{y1}")
            new_t.text = merged_text
            cell.append(new_t)


def recursively_indent(elem, level=0):
    indent = "\n" + ("  " * level)
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        for child in elem:
            recursively_indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent
