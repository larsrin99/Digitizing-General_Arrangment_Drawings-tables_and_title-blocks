# src/utils.py

import math
from typing import List, Tuple
from shapely.geometry import LineString, Point
from .data_structures import CurveSegment

BBox = Tuple[float, float, float, float]  # (x0, y0, x1, y1)

def parse_bbox(bbox_str: str) -> BBox:
    return tuple(map(float, bbox_str.strip().split(",")))

def bbox_to_str(bbox: BBox, precision=3) -> str:
    return ",".join(f"{v:.{precision}f}" for v in bbox)

def bbox_area(bbox: BBox) -> float:
    x0, y0, x1, y1 = bbox
    return abs((x1 - x0) * (y1 - y0))

def bbox_center(bbox: BBox) -> Tuple[float, float]:
    x0, y0, x1, y1 = bbox
    return ((x0 + x1) / 2, (y0 + y1) / 2)

def bbox_contains_point(bbox: BBox, x: float, y: float) -> bool:
    x0, y0, x1, y1 = bbox
    return x0 <= x <= x1 and y0 <= y <= y1

def bbox_is_contained(inner: BBox, outer: BBox) -> bool:
    ix0, iy0, ix1, iy1 = inner
    ox0, oy0, ox1, oy1 = outer
    return ox0 <= ix0 and oy0 <= iy0 and ox1 >= ix1 and oy1 >= iy1


def calculate_distance_point_to_line(point: Tuple[float, float],
                                      line_start: Tuple[float, float],
                                      line_end: Tuple[float, float]) -> float:
    """Calculates the minimum distance from a point to a line segment."""
    # Handle potential degenerate line segment (start == end)
    if math.dist(line_start, line_end) < 1e-9: # Use a small epsilon
        return math.dist(point, line_start)

    shapely_point = Point(point)
    shapely_line = LineString([line_start, line_end])
    return shapely_point.distance(shapely_line)

def is_straight(curve: CurveSegment, tolerance: float) -> bool:
    """
    Checks if a CurveSegment represents a straight line within a given tolerance.
    """
    if not curve.points or len(curve.points) < 2:
        return False
    if len(curve.points) == 2:
        return True

    start_point = curve.points[0]
    end_point = curve.points[-1]

    # --- REMOVED the check comparing start/end distance to tolerance ---

    # Check distance of all intermediate points to the line defined by start and end
    max_deviation = 0.0
    failing_point_idx = -1
    for i in range(1, len(curve.points) - 1):
        intermediate_point = curve.points[i]
        # Use the refined distance calculation
        distance = calculate_distance_point_to_line(intermediate_point, start_point, end_point)
        if distance > tolerance:
            # Store details of failure for debugging
            max_deviation = distance
            failing_point_idx = i
            print(f"DEBUG is_straight: FAILING - Point {i} {intermediate_point} distance {distance:.4f} > tolerance {tolerance:.4f}")
            return False # Point deviates too much

    print(f"DEBUG is_straight: PASSING for curve with {len(curve.points)} points.")
    return True


def parse_elements_from_xml(xml_root):
    """Parses structured PageElements from raw XML."""
    elements_by_page = {}
    pages = xml_root.xpath("//page")
    for page_num, page in enumerate(pages, start=1):
        page_elements = []

        # Lines
        for line in page.xpath(".//line"):
            try:
                x0 = float(line.get("x0"))
                y0 = float(line.get("y0"))
                x1 = float(line.get("x1"))
                y1 = float(line.get("y1"))
                linewidth = float(line.get("linewidth", "0.5"))
                page_elements.append(LineSegment(bbox=(x0, y0, x1, y1), page_number=page_num,
                                                 start=(x0, y0), end=(x1, y1), linewidth=linewidth))
            except:
                continue

        # Curves
        for curve in page.xpath(".//curve"):
            try:
                points = []
                for pt in curve.xpath(".//pt"):
                    x = float(pt.get("x"))
                    y = float(pt.get("y"))
                    points.append((x, y))
                linewidth = float(curve.get("linewidth", "0.5"))
                page_elements.append(CurveSegment(points=points, page_number=page_num, linewidth=linewidth))
            except:
                continue

        # Textboxes
        for textbox in page.xpath(".//textbox"):
            try:
                x0 = float(textbox.get("x0"))
                y0 = float(textbox.get("y0"))
                x1 = float(textbox.get("x1"))
                y1 = float(textbox.get("y1"))
                text_content = "".join(textbox.itertext()).strip()
                page_elements.append(TextBox(bbox=(x0, y0, x1, y1), page_number=page_num, text=text_content))
            except:
                continue

        elements_by_page[page_num] = page_elements
    return elements_by_page



from shapely.geometry import LineString

def bbox_to_linestring(bbox_str):
    x0, y0, x1, y1 = map(float, bbox_str.split(","))
    return LineString([(x0, y0), (x1, y1)])
