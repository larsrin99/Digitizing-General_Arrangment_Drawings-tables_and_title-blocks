from lxml import etree

def extract_margin_lines(xml_path):
    tree = etree.parse(xml_path)
    root = tree.getroot()

    page_elem = root.find(".//page")
    page_bbox = list(map(float, page_elem.get("bbox").split(",")))
    page_width = page_bbox[2]
    page_height = page_bbox[3]

    EPSILON = 2
    MIN_LENGTH = 10
    MAX_WIDTH_FRAC = 0.95
    MAX_HEIGHT_FRAC = 0.95

    horizontal_lines = []
    vertical_lines = []

    for line in root.findall(".//line"):
        bbox = list(map(float, line.get("bbox").split(",")))
        x0, y0, x1, y1 = bbox
        if abs(y1 - y0) < EPSILON:  # horizontal
            length = abs(x1 - x0)
            if length >= MIN_LENGTH and length <= MAX_WIDTH_FRAC * page_width:
                horizontal_lines.append({"bbox": bbox, "length": length})
        elif abs(x1 - x0) < EPSILON:  # vertical
            length = abs(y1 - y0)
            if length >= MIN_LENGTH and length <= MAX_HEIGHT_FRAC * page_height:
                vertical_lines.append({"bbox": bbox, "length": length})

    if not vertical_lines or not horizontal_lines:
        raise ValueError("No valid horizontal or vertical margin candidates found.")

    # Get the longest horizontal and vertical lines
    top_horizontal_lines = sorted(horizontal_lines, key=lambda l: l["length"], reverse=True)[:2]
    top_vertical_lines = sorted(vertical_lines, key=lambda l: l["length"], reverse=True)[:2]

    print("Top 2 horizontal lines:")
    for line in top_horizontal_lines:
        print(f"  {line['bbox']} — length {line['length']:.1f}")

    print("Top 2 vertical lines:")
    for line in top_vertical_lines:
        print(f"  {line['bbox']} — length {line['length']:.1f}")

    print(top_horizontal_lines[0]["bbox"], top_vertical_lines[0]["bbox"])

    return top_horizontal_lines[0]["bbox"], top_vertical_lines[0]["bbox"]
