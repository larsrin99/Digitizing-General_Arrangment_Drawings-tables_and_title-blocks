import json
import os
from datetime import datetime
from lxml import etree

VALIDATION_CATEGORIES = ["valid", "empty", "missing"]

class Validator:
    def __init__(self, xml_path, isofields_path):
        self.xml_path = xml_path
        self.isofields_path = isofields_path
        self.report = {}
        self.tree = etree.parse(xml_path)
        self.root = self.tree.getroot()
        with open(isofields_path, "r") as f:
            self.field_definitions = json.load(f)

    def validate_titleblock_fields(self):
        expected_fields = set(self.field_definitions.keys())
        present_fields = {
            field.get("id"): (field.text or "").strip()
            for field in self.root.findall(".//document_property")
        }

        for field_id in expected_fields:
            value = present_fields.get(field_id, None)
            if value is None:
                self.report[field_id] = "missing"
            elif value.strip() in ["", "-", " "]:
                self.report[field_id] = "empty"
            else:
                self.report[field_id] = "valid"

        return self.report

    def print_report(self):
        print("\nValidation Report:")
        for field, status in self.report.items():
            print(f"- {field}: {status}")

    def get_issues(self, include_valid=False):
        return {
            k: v for k, v in self.report.items()
            if include_valid or v != "valid"
        }

    def write_json_report(self):
        """Writes validation results to a JSON file in the same folder as the XML document."""
        document_type = self.root.get("type")
        doc_number_elem = self.root.find(".//document_property[@id='document_number']")
        document_number = doc_number_elem.text.strip() if doc_number_elem is not None else "UNKNOWN"

        report_data = {
            "document_type": document_type,
            "document_number": document_number,
            "validation_timestamp": datetime.utcnow().isoformat(),
            "titleblock": {
                "field_statuses": self.report,
                "missing_fields": [k for k, v in self.report.items() if v == "missing"],
                "empty_fields": [k for k, v in self.report.items() if v == "empty"],
            }
        }

        folder = os.path.dirname(self.xml_path)
        base_name = os.path.splitext(os.path.basename(self.xml_path))[0]
        json_report_path = os.path.join(folder, f"{base_name}_validation.json")

        with open(json_report_path, "w") as f:
            json.dump(report_data, f, indent=4)

        print(f"\nJSON validation report saved to {json_report_path}")
