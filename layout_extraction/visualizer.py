# visualizer.py
#
# Blank-canvas debug figures for the layout-extraction pipeline.
# Produces:
#   • draw_lines()          – Fig-1
#   • draw_intersections()  – Fig-2
#   • draw_rectangles()     – Fig-3
#   • draw_text_assignment()– Fig-4
#
# All coordinates assume a PDF-style origin (0, 0) at **top-left**.

import logging
from pathlib import Path
from typing import Iterable, Tuple, Sequence

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle

logger = logging.getLogger(__name__)

__all__ = [
    "LineVisualizer",
]


FONT = FontProperties(family="DejaVu Sans", size=6)


class LineVisualizer:
    """Utility class for generating pipeline debug figures."""

    @staticmethod
    def _setup_axes(page_width: float, page_height: float, dpi: int = 100):
        fig = plt.figure(figsize=(page_width / dpi, page_height / dpi), dpi=dpi)
        ax = fig.add_subplot(111)
        ax.set_xlim(0, page_width)
        ax.set_ylim(page_height, 0)
        ax.set_aspect("equal")
        ax.axis("off")
        return fig, ax

    def draw_lines(
        self,
        horiz_lines: Sequence[dict],
        vert_lines: Sequence[dict],
        page_width: float,
        page_height: float,
        output_path: Path | str,
        *,
        intersections: Iterable[Tuple[float, float]] | None = None,
        filtered_horiz: Sequence[dict] | None = None,
        filtered_vert: Sequence[dict] | None = None,
        margin_horiz: Sequence[dict] | None = None,
        margin_vert: Sequence[dict] | None = None,
    ) -> None:
        fig, ax = self._setup_axes(page_width, page_height)

        def _draw(lines, color, lw):
            for ln in lines or []:
                bbox = ln["bbox"]
                if isinstance(bbox, str):
                    x0, y0, x1, y1 = map(float, bbox.split(","))
                else:
                    x0, y0, x1, y1 = bbox
                ax.plot([x0, x1], [y0, y1], color=color, linewidth=lw)

        _draw(horiz_lines,    "black", 0.5)
        _draw(vert_lines,     "black", 0.5)
        _draw(filtered_horiz, "blue",  1.0)
        _draw(filtered_vert,  "blue",  1.0)
        _draw(margin_horiz,   "green", 1.5)
        _draw(margin_vert,    "green", 1.5)

        if intersections:
            xs, ys = zip(*intersections)
            ax.scatter(xs, ys, s=6, c="red")

        fig.savefig(output_path, bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        logger.info("✅ Saved line visualization → %s", output_path)

    def draw_intersections(
        self,
        points: Iterable[Tuple[float, float]],
        page_width: float,
        page_height: float,
        output_path: Path | str,
    ) -> None:
        fig, ax = self._setup_axes(page_width, page_height)
        if points:
            xs, ys = zip(*points)
            ax.scatter(xs, ys, s=6, c="red")
        fig.savefig(output_path, bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        logger.info("✅ Saved intersections → %s", output_path)

    def draw_rectangles(
        self,
        rectangles: Sequence[dict],
        page_width: float,
        page_height: float,
        output_path: Path | str,
    ) -> None:
        fig, ax = self._setup_axes(page_width, page_height)
        for rect in rectangles:
            bbox = rect.get("bbox")
            if isinstance(bbox, str):
                x0, y0, x1, y1 = map(float, bbox.split(","))
            else:
                x0, y0, x1, y1 = bbox
            xmin, ymin = min(x0, x1), min(y0, y1)
            w, h = abs(x1 - x0), abs(y1 - y0)
            ax.add_patch(
                Rectangle(
                    (xmin, ymin),
                    w,
                    h,
                    linewidth=1.0,
                    edgecolor="red",
                    facecolor="none",
                )
            )
        fig.savefig(output_path, bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        logger.info("✅ Saved rectangle visualization → %s", output_path)

    def draw_text_assignment(
        self,
        tables: Sequence,
        page_width: float,
        page_height: float,
        output_path: Path | str,
    ) -> None:
        fig, ax = self._setup_axes(page_width, page_height)

        for tbl in tables:
            for cell in tbl.cells:
                x0, y0, x1, y1 = cell.bbox
                xmin, ymin = min(x0, x1), min(y0, y1)
                w, h = abs(x1 - x0), abs(y1 - y0)
                ax.add_patch(
                    Rectangle(
                        (xmin, ymin),
                        w,
                        h,
                        linewidth=0.8,
                        edgecolor="black",
                        facecolor=(0.6, 0.8, 1.0, 0.3),
                    )
                )
                ax.text(
                    xmin + 2,
                    ymin + 8,
                    cell.text[:30].replace("\n", " "),
                    fontproperties=FONT,
                    color="black",
                    va="top",
                )

        fig.savefig(output_path, bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        logger.info("✅ Saved table-text visualization → %s", output_path)
