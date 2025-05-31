import os
from io import BytesIO
from pathlib import Path
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
try:
    from lxml import etree as ET
except ImportError:
    print("Warning: lxml not found. Falling back to xml.etree.ElementTree.")
    import xml.etree.ElementTree as ET
from .config import PDFMINER_COMMAND
import logging

class PdfConverter:
    def __init__(self, output_folder: str = "data/output"):
        self.output_folder = output_folder
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def convert(self, pdf_path: str, output_xml_path: str):
        if not os.path.exists(pdf_path):
            self.logger.error(f"❌ Input PDF not found: {pdf_path}")
            return None

        self.logger.info(f"Starting PDF to XML conversion for: {pdf_path}")
        try:
            laparams = LAParams(
                line_margin=0.05,
                detect_vertical=True,
                char_margin=0.5,
                word_margin=0.2,
                boxes_flow=0.5
            )

            xml_output = BytesIO()
            with open(pdf_path, "rb") as pdf_file:
                extract_text_to_fp(pdf_file, xml_output, output_type="xml", laparams=laparams)

            xml_output.seek(0)
            xml_content = xml_output.read()
            if not xml_content:
                self.logger.error(f"❌ No XML output from pdfminer for {pdf_path}")
                return None

            root = ET.fromstring(xml_content) if ET.__name__ == "lxml.etree" else ET.fromstring(xml_content.decode('utf-8'))

            # Patch zero-width lines
            self.logger.info("Patching zero-width lines...")
            all_lines = root.xpath(".//line[@linewidth]") if ET.__name__ == "lxml.etree" else [
                elem for elem in root.findall('.//line') if 'linewidth' in elem.attrib
            ]
            line_widths = [float(line.get("linewidth", "0")) for line in all_lines if float(line.get("linewidth", "0")) > 0]
            min_nonzero_width = min(line_widths) if line_widths else 0.5
            patched_count = 0
            for line in all_lines:
                if float(line.get("linewidth", "0")) == 0:
                    line.set("linewidth", str(min_nonzero_width))
                    patched_count += 1
            self.logger.info(f"Patched {patched_count} zero-width lines.")

            # Save XML
            os.makedirs(os.path.dirname(output_xml_path), exist_ok=True)
            tree = ET.ElementTree(root)
            write_kwargs = {"encoding": "utf-8", "xml_declaration": True}
            if ET.__name__ == "lxml.etree":
                write_kwargs["pretty_print"] = True
            tree.write(str(output_xml_path), **write_kwargs)

            self.logger.info(f"✅ Saved XML to: {output_xml_path}")
            return str(output_xml_path), tree

        except Exception as e:
            self.logger.error(f"❌ Error converting {pdf_path}: {e}", exc_info=True)
            return None

    def convert_and_parse(self, pdf_path: str) -> list:
        stem = Path(pdf_path).stem
        output_xml_path = os.path.join(self.output_folder, f"{stem}_raw_output.xml")

        result = self.convert(pdf_path, output_xml_path)
        if result is None:
            return []

        _, tree = result
        root = tree.getroot()
        pages = []

        for i, page_el in enumerate(root.findall(".//page")):
            try:
                page_num = int(page_el.attrib.get("id", f"{i+1}").replace("page", ""))
            except ValueError:
                page_num = i + 1
            width = float(page_el.attrib.get("width", "1000"))
            height = float(page_el.attrib.get("height", "1000"))
            textboxes = page_el.findall(".//textbox")

            pages.append({
                "page_num": page_num,
                "width": width,
                "height": height,
                "element": page_el,
                "textboxes": textboxes
            })

        return pages
