# orchestrator.py

import os
from lxml import etree
from semantic_annotation.intersection_loader import IntersectionLoader
from semantic_annotation.region_classifier import RegionClassifier
from semantic_annotation.margin_utils import extract_margin_lines
from semantic_annotation.table_structurer import TableStructurer, recursively_indent, merge_column_texts, merge_cell_texts_by_y0
from semantic_annotation.title_block import TitleBlockOrganizer
from semantic_annotation.rdl_mapper import RDLMapper
from semantic_annotation.rdf_builder import RDFBuilder
  

class PDFLayoutProcessor:
    def __init__(self, output_dir, isofields_path, rdl_ttl_path):
        self.output_dir = output_dir
        self.isofields_path = isofields_path
        self.rdl_ttl_path = rdl_ttl_path

    def run(self):
        for filename in os.listdir(self.output_dir):
            if not filename.endswith("_rectangles_merged.xml"):
                continue

            page_prefix = filename.replace("_rectangles_merged.xml", "")
            rects_path = os.path.join(self.output_dir, filename)
            intersections_path = os.path.join(self.output_dir, f"{page_prefix}_intersections.xml")
            raw_path = os.path.join(self.output_dir, "raw_output.xml")
            debug_path = os.path.join(self.output_dir, f"{page_prefix}_structured_debug.xml")
            output_path = os.path.join(self.output_dir, f"{page_prefix}_structured_output.xml")
            enriched_path = os.path.join(self.output_dir, f"{page_prefix}_enriched_output.xml")

            print(f"\n📄 Processing {page_prefix}")

            # Load intersections
            intersections = IntersectionLoader(intersections_path).load()

            # Parse rectangles
            rect_tree = etree.parse(rects_path)
            rect_root = rect_tree.getroot()

            # Generate structured rectangles
            rect_root = RegionClassifier(rect_root, intersections).apply()
            if rect_root is None:
                raise RuntimeError("RegionClassifier returned None")

            # Margin lines
            bottom_line_bbox, right_line_bbox = extract_margin_lines(raw_path)

            # Classify tables and fields
            TableStructurer(rect_root, bottom_line_bbox, right_line_bbox).apply()
            TitleBlockOrganizer(rect_root).detect_revision_table()

            merge_column_texts(rect_root)
            merge_cell_texts_by_y0(rect_root)
            

            # Save debug version
            etree.ElementTree(rect_root).write(debug_path, pretty_print=True, encoding="utf-8", xml_declaration=True)

            TitleBlockOrganizer(rect_root).detect_titleblock_fields(self.isofields_path)
            
            recursively_indent(rect_root)

            etree.ElementTree(rect_root).write(output_path, pretty_print=True, encoding="utf-8", xml_declaration=True)
            print(f"✅ Saved structured XML: {output_path}")

            # RDL enrichment
            rdl_mapper = RDLMapper(self.rdl_ttl_path)
            rdl_mapper.enrich(output_path, enriched_path)

            pdf_name = self.output_dir.name
            # === RDF Generation ===
            try:
                rdf_builder = RDFBuilder(schema_path=self.rdl_ttl_path)
                rdf_builder.generate_rdf_from_xml(pdf_name)
            except Exception as e:
                print(f"⚠️ RDF generation failed for {pdf_name}: {e}")
