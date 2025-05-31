# pipeline/rectangle_processor.py
from lxml import etree
from semantic_annotation.bbox_utils import parse_bbox, bbox_contains, point_inside_bbox

class RegionClassifier:
    def __init__(self, root, intersection_points):
        self.root = root
        self.intersection_points = intersection_points

    def apply(self):
        for rect in self.root.findall("rectangle"):
            bbox = parse_bbox(rect.attrib["bbox"])
            rect_texts = rect.findall("text")

            # Add intersection points inside rectangle
            local_points = [
                (x, y) for (x, y) in self.intersection_points
                if point_inside_bbox(x, y, bbox)
            ]
            for x, y in local_points:
                etree.SubElement(rect, "intersection", attrib={"x": str(x), "y": str(y)})

            # Detect grid cells based on intersections
            cells = []
            for (x0, y0) in local_points:
                right = sorted([(x, y0) for (x, y) in local_points if y == y0 and x > x0], key=lambda p: p[0])
                below = sorted([(x0, y) for (x, y) in local_points if x == x0 and y > y0], key=lambda p: p[1])
                if right and below:
                    cells.append((x0, y0, right[0][0], below[0][1]))

            # Assign text to cells
            text_data = [{"bbox": parse_bbox(t.attrib["bbox"]), "element": t} for t in rect_texts]
            used_texts = set()

            for (x0, y0, x1, y1) in cells:
                cell_bbox = [x0, y0, x1, y1]
                inside_texts = [td for td in text_data if bbox_contains(cell_bbox, td["bbox"])]
                if inside_texts:
                    cell_elem = etree.Element("cell", attrib={"bbox": f"{x0:.2f},{y0:.2f},{x1:.2f},{y1:.2f}"})
                    for td in inside_texts:
                        text = etree.Element("text", attrib={
                            "bbox": ",".join(f"{v:.3f}" for v in td["bbox"])
                        })
                        text.text = td["element"].text
                        cell_elem.append(text)
                        used_texts.add(td["element"])
                    rect.append(cell_elem)

            for txt in used_texts:
                rect.remove(txt)
        return self.root