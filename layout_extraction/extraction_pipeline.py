from pathlib import Path
import logging

from layout_extraction.pdf_converter import PdfConverter
from layout_extraction.line_extractor import LineExtractor
from layout_extraction.visualizer import LineVisualizer
from layout_extraction.intersection_finder import IntersectionFinder
from layout_extraction.rectangle_detector import RectangleDetector
from layout_extraction.textbox_mapper import TextboxMapper
from layout_extraction.rectangle_merger import (
    merge_rectangles_distinct,
    export_rectangles_to_xml,
)
from layout_extraction.stats_collector import StatsCollector
from layout_extraction.reporter import (
    write_summary_csv,
    summary_dataframe,
    write_xml_excerpt,
)

log = logging.getLogger(__name__)


class LayoutExtractionPipeline:
    def __init__(self, debug_dir: Path | None = None):
        self.debug_dir = Path(debug_dir or "debug_output")
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        log.info("Summary/debug files will be saved to %s", self.debug_dir.resolve())

        self.converter = PdfConverter()
        self.extractor = LineExtractor()
        self.visualizer = LineVisualizer()
        self.finder = IntersectionFinder()
        self.stats = StatsCollector()
        self.images_dir = None

    def _debug_path(self, page_tag: str, label: str) -> Path:
        return self.images_dir / f"{page_tag}_{label}.png"
    
    def _extract_page_dimensions(self, page_elem) -> tuple[float, float]:
        bbox_str = page_elem.attrib.get("bbox", "0,0,1000,1000")
        _, _, x1, y1 = map(float, bbox_str.split(","))
        return x1, y1

    def process(self, pdf_path: Path, out_dir: Path) -> Path:
        pdf_path = Path(pdf_path)
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        self.images_dir = out_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

        # Convert PDF and get list of page dicts
        pages = self.converter.convert_and_parse(pdf_path)
        log.info("Loaded %d pages from '%s'", len(pages), pdf_path.name)

        all_tables = []

        for page in pages:
            page_num = page["page_num"]
            W, H = self._extract_page_dimensions(page["element"])
            page_tag = f"p{page_num:04d}"
            self.stats.pages += 1

            horiz, vert = self.extractor.extract_lines(page["element"])
            self.stats.add_line_counts(len(horiz), len(vert))

            intersections = self.finder.compute_intersections(horiz, vert)

            detector = RectangleDetector(intersections)
            rects_raw = detector.detect()
            self.stats.add_rect_init(len(rects_raw))

            mapper = TextboxMapper(rects_raw, page["textboxes"])
            rects_mapped = mapper.map_textboxes()

            rects = merge_rectangles_distinct(rects_mapped)
            self.stats.add_rect_merged(len(rects))

            tables = rects
            for tbl in tables:
                self.stats.add_table(tbl.get("n_rows", 0), tbl.get("n_cols", 0))
            all_tables.extend(tables)

            # Visualizations (always saved)
            self.visualizer.draw_lines(
                horiz, vert, W, H,
                self._debug_path(page_tag, "lines"),
                intersections=None,
            )
            self.visualizer.draw_intersections(
                intersections, W, H,
                self._debug_path(page_tag, "pts")
            )
            self.visualizer.draw_rectangles(
                rects, W, H,
                self._debug_path(page_tag, "rects")
            )
            # Uncomment when rects are structured with .cells
            # self.visualizer.draw_text_assignment(
            #     tables, W, H,
            #     self._debug_path(page_tag, "tables")
            # )

        # Write summary + XML output
        summary = self.stats.as_summary()
        write_summary_csv(summary, self.debug_dir / "summary.csv")
        print("\nPipeline Summary:")
        print(summary_dataframe(summary).to_string(index=False), "\n")

        output_xml_path = out_dir / "rectangles_output.xml"
        export_rectangles_to_xml(all_tables, output_xml_path)
        write_xml_excerpt(output_xml_path, self.debug_dir / "xml_excerpt.xml")
        log.info("✅ Layout pipeline complete → %s", output_xml_path.resolve())
        return output_xml_path
