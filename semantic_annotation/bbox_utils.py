# pipeline/bbox_utils.py

def parse_bbox(bbox_str):
    return list(map(float, bbox_str.split(",")))

def format_bbox(bbox):
    return ",".join(f"{x:.2f}" for x in bbox)

def bbox_contains(container, inner):
    x0, y0, x1, y1 = container
    xi0, yi0, xi1, yi1 = inner
    return x0 <= xi0 and y0 <= yi0 and x1 >= xi1 and y1 >= yi1

def point_inside_bbox(x, y, bbox):
    x0, y0, x1, y1 = bbox
    return x0 <= x <= x1 and y0 <= y <= y1