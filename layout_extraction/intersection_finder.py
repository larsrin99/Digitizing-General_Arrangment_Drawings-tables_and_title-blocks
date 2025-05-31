import logging
from shapely.geometry import LineString

logger = logging.getLogger(__name__)

class IntersectionFinder:
    def __init__(self):
        self.intersections = set()
        self.margin_lines = {
            "horizontal": [],
            "vertical": []
        }
        self.filtered_lines = {
            "horizontal": [],
            "vertical": []
        }

    def filter_lines(self, lines, orientation, page_width, page_height, keep_margin_lines=True):
        MIN_LENGTH = 10
        MARGIN = 50

        # Sort lines by length and keep the two longest as margins
        sorted_by_length = sorted(lines, key=lambda l: l["length"], reverse=True)
        margin = sorted_by_length[:2] if keep_margin_lines else []

        filtered = []
        for l in lines:
            try:
                x0, y0, x1, y1 = map(float, l["bbox"].split(","))
                if l["length"] < MIN_LENGTH:
                    continue

                if orientation == "horizontal":
                    if not (MARGIN < x0 < (page_width - MARGIN)):
                        continue
                elif orientation == "vertical":
                    if not (MARGIN < y0 < (page_height - MARGIN)):
                        continue
                filtered.append(l)
            except Exception as e:
                logger.warning(f"Skipping line due to parsing error: {l} — {e}")

        self.margin_lines[orientation] = margin
        self.filtered_lines[orientation] = filtered
        return filtered + margin

    def compute_intersections(self, horizontal_lines, vertical_lines):
        logger.info("Finding intersections between horizontal and vertical lines...")

        h_geoms = []
        v_geoms = []

        for line in horizontal_lines:
            try:
                x0, y0, x1, y1 = map(float, line["bbox"].split(","))
                h_geoms.append(LineString([(x0, y0), (x1, y1)]))
            except Exception as e:
                logger.warning(f"Skipping horizontal line {line} due to {e}")

        for line in vertical_lines:
            try:
                x0, y0, x1, y1 = map(float, line["bbox"].split(","))
                v_geoms.append(LineString([(x0, y0), (x1, y1)]))
            except Exception as e:
                logger.warning(f"Skipping vertical line {line} due to {e}")

        for h in h_geoms:
            for v in v_geoms:
                try:
                    inter = h.intersection(v)
                    if inter.is_empty:
                        continue

                    if inter.geom_type == "Point":
                        self.intersections.add((round(inter.x, 3), round(inter.y, 3)))
                    elif inter.geom_type in {"MultiPoint", "GeometryCollection"}:
                        for pt in getattr(inter, 'geoms', []):
                            if pt.geom_type == "Point":
                                self.intersections.add((round(pt.x, 3), round(pt.y, 3)))
                except Exception as e:
                    logger.warning(f"Intersection failed between {h} and {v}: {e}")

        logger.info(f"Found {len(self.intersections)} unique intersections.")
        return list(self.intersections)

    def export_as_points(self):
        return [{"x": x, "y": y} for x, y in sorted(self.intersections)]