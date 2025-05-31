import logging
from typing import List, Dict, Tuple, Optional
from shapely.geometry import box
from .utils import bbox_area

logger = logging.getLogger(__name__)

BoundingBox = Tuple[float, float, float, float]


class RectangleDetector:
    def __init__(
        self,
        intersections: List[Tuple[float, float]],
        horiz_lines: Optional[List] = None,
        vert_lines: Optional[List] = None,
        tolerance: float = 1.5,
        max_width: float = 1500,
        max_height: float = 1000,
        min_width: float = 10,
        min_height: float = 10,
    ):
        """
        Rectangle detector using intersection points and optional grid lines.

        Args:
            intersections: List of (x, y) tuples representing intersection points.
            horiz_lines: Optional horizontal lines (unused in current implementation).
            vert_lines: Optional vertical lines (unused in current implementation).
            tolerance: Tolerance for matching corners.
            max_width, max_height: Bounding box max constraints.
            min_width, min_height: Bounding box min constraints.
        """
        self.intersections = intersections
        self.horiz_lines = horiz_lines or []
        self.vert_lines = vert_lines or []
        self.tolerance = tolerance
        self.max_width = max_width
        self.max_height = max_height
        self.min_width = min_width
        self.min_height = min_height
        self.rectangles: List[Dict] = []

        # Fast lookup for corner matching
        self.point_index = {
            (round(x, 1), round(y, 1)): (x, y) for x, y in intersections
        }

    def _point_exists(self, x_target: float, y_target: float) -> Optional[Tuple[float, float]]:
        for dx in [-self.tolerance, 0, self.tolerance]:
            for dy in [-self.tolerance, 0, self.tolerance]:
                key = (round(x_target + dx, 1), round(y_target + dy, 1))
                if key in self.point_index:
                    return self.point_index[key]
        return None

    def _rect_key(self, corners: List[Tuple[float, float]]) -> Tuple:
        return tuple(sorted((round(x, 2), round(y, 2)) for x, y in corners))

    def detect(self) -> List[Dict]:
        """Main entry point: detects rectangles from intersection points."""
        logger.info("Detecting rectangles using grid-based corner matching...")
        seen = set()
        rectangles = []
        pts = list(self.intersections)

        for i, (x1, y1) in enumerate(pts):
            for x2, y2 in pts[i + 1:]:
                if abs(y1 - y2) <= self.tolerance or abs(x1 - x2) <= self.tolerance:
                    continue

                width = abs(x2 - x1)
                height = abs(y2 - y1)
                if width > self.max_width or height > self.max_height:
                    continue
                if width < self.min_width or height < self.min_height:
                    continue

                p3 = self._point_exists(x1, y2)
                p4 = self._point_exists(x2, y1)

                if p3 and p4:
                    all_pts = [(x1, y1), (x2, y2), p3, p4]
                    key = self._rect_key(all_pts)
                    if key in seen:
                        continue
                    seen.add(key)

                    x_min, x_max = sorted([x1, x2])
                    y_min, y_max = sorted([y1, y2])

                    rect = {
                        "bbox": (x_min, y_min, x_max, y_max),
                        "coords": [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)],
                    }
                    rectangles.append(rect)

        logger.info(f"Detected {len(rectangles)} raw rectangles. Filtering large containers...")
        rectangles = self.remove_large_containers(rectangles)
        logger.info(f"✅ Final rectangle count: {len(rectangles)}")

        self.rectangles = rectangles
        return rectangles

    def remove_large_containers(self, rectangles: List[Dict]) -> List[Dict]:
        """Removes rectangles that are fully contained inside larger ones."""
        filtered = []
        for rect in rectangles:
            contained = False
            r_box = box(*rect["bbox"])
            for other in rectangles:
                if rect == other:
                    continue
                o_box = box(*other["bbox"])
                if o_box.contains(r_box):
                    contained = True
                    break
            if not contained:
                filtered.append(rect)
        return filtered
