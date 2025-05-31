# line_extractor.py

from lxml import etree

class LineExtractor:
    def __init__(self):
        self.horizontal_lines = []
        self.vertical_lines = []

    def extract_lines(self, root):
        seen_lines = set()

        # Handle <line> elements
        for line in root.xpath(".//line"):
            bbox = line.get("bbox")
            if not bbox:
                continue
            rounded = ",".join([f"{float(x):.1f}" for x in bbox.split(",")])
            if rounded in seen_lines:
                continue
            seen_lines.add(rounded)

            x_min, y_min, x_max, y_max = map(float, bbox.split(","))
            length_horizontal = abs(x_max - x_min)
            length_vertical = abs(y_max - y_min)

            if length_horizontal >= 2 and abs(y_max - y_min) < 5:
                self.horizontal_lines.append({"length": round(length_horizontal, 4), "bbox": bbox})
            elif length_vertical >= 2 and abs(x_max - x_min) < 5:
                self.vertical_lines.append({"length": round(length_vertical, 4), "bbox": bbox})

        # Handle <curve> elements
        for curve in root.xpath(".//curve[@pts]"):
            pts = curve.get("pts")
            if not pts:
                continue
            points = self.parse_curve_points(pts)

            # Option A: Whole curve is line-like
            line_type = self.is_line_like_curve(points)
            if line_type:
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]

                if line_type == "horizontal":
                    x0, x1 = min(xs), max(xs)
                    y0 = y1 = round(sum(ys) / len(ys), 3)
                else:
                    y0, y1 = min(ys), max(ys)
                    x0 = x1 = round(sum(xs) / len(xs), 3)

                bbox = f"{x0:.3f},{y0:.3f},{x1:.3f},{y1:.3f}"
                rounded = ",".join([f"{float(x):.1f}" for x in bbox.split(",")])
                if rounded not in seen_lines:
                    seen_lines.add(rounded)
                    length = abs(x1 - x0) if line_type == "horizontal" else abs(y1 - y0)
                    if length >= 2:
                        line_data = {"length": round(length, 4), "bbox": bbox}
                        if line_type == "horizontal":
                            self.horizontal_lines.append(line_data)
                        else:
                            self.vertical_lines.append(line_data)
                continue

            # Option B: Curve has short segments that look like lines
            for i in range(len(points) - 1):
                (x0, y0), (x1, y1) = points[i], points[i + 1]
                dx = abs(x1 - x0)
                dy = abs(y1 - y0)

                if dx >= 2 and dy < 1.5:
                    y_avg = round((y0 + y1) / 2, 3)
                    bbox = f"{min(x0, x1):.3f},{y_avg:.3f},{max(x0, x1):.3f},{y_avg:.3f}"
                    rounded = ",".join([f"{float(x):.1f}" for x in bbox.split(",")])
                    if rounded not in seen_lines:
                        self.horizontal_lines.append({"length": round(dx, 4), "bbox": bbox})
                        seen_lines.add(rounded)

                elif dy >= 2 and dx < 1.5:
                    x_avg = round((x0 + x1) / 2, 3)
                    bbox = f"{x_avg:.3f},{min(y0, y1):.3f},{x_avg:.3f},{max(y0, y1):.3f}"
                    rounded = ",".join([f"{float(x):.1f}" for x in bbox.split(",")])
                    if rounded not in seen_lines:
                        self.vertical_lines.append({"length": round(dy, 4), "bbox": bbox})
                        seen_lines.add(rounded)

        return self.horizontal_lines, self.vertical_lines

    def parse_curve_points(self, pts_str):
        vals = list(map(float, pts_str.strip().split(",")))
        return [(vals[i], vals[i + 1]) for i in range(0, len(vals), 2)]

    def is_line_like_curve(self, points):
        if len(points) < 2:
            return None
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        dx = max(xs) - min(xs)
        dy = max(ys) - min(ys)

        if dx >= 2 and dy < 1.5:
            return "horizontal"
        elif dy >= 2 and dx < 1.5:
            return "vertical"
        else:
            return None

    def reset(self):
        self.horizontal_lines = []
        self.vertical_lines = []
