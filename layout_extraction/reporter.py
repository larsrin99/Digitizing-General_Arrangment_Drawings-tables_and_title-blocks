from pathlib import Path
import csv
import pandas as pd
from lxml import etree


def write_summary_csv(summary: dict, out_path: Path):
    with open(out_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Metric", "Value"])
        for k, v in summary.items():
            w.writerow([k, v])


def summary_dataframe(summary: dict) -> pd.DataFrame:
    return pd.DataFrame(list(summary.items()), columns=["Metric", "Value"])


def write_xml_excerpt(xml_path: Path, out_path: Path):
    tree = etree.parse(str(xml_path))
    table = tree.find(".//table")
    if table is not None:
        out_path.write_text(etree.tostring(table, pretty_print=True).decode())