import os
import time
import argparse
from pathlib import Path
from layout_extraction.extraction_pipeline import LayoutExtractionPipeline
from semantic_annotation.orchestrator import PDFLayoutProcessor
from validator import Validator

def list_pdfs(input_dir):
    return [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]

def choose_option(options, prompt="Choose an option:"):
    for i, option in enumerate(options, 1):
        print(f"{i}: {option}")
    idx = int(input(prompt)) - 1
    return options[idx]

def find_enriched_xml(output_dir):
    for fname in os.listdir(output_dir):
        if fname.endswith("_enriched_output.xml"):
            return output_dir / fname
    raise FileNotFoundError("No enriched XML file found in output directory.")

def main():
    parser = argparse.ArgumentParser(description="Run layout pipeline")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--debug-dir", type=Path, help="Optional debug output directory")
    args = parser.parse_args()

    input_dir = Path("data/input/")
    output_base = Path("data/output/")
    config_dir = Path("data/config/")
    isofields_path = config_dir / "iso7200_fields.json"
    rdl_ttl_path = config_dir / "ISO 15926 Part 4 - v.4.ttl"

    pdf_files = list_pdfs(input_dir)
    print("Select a PDF:")
    pdf_choice = choose_option(pdf_files)
    input_pdf_path = input_dir / pdf_choice
    output_dir = output_base / pdf_choice.rsplit(".", 1)[0]

    print("\nChoose a pipeline to run:")
    pipeline_options = [
        "1. Extract Lines + Rectangles",
        "2. Classify + Annotate + Enrich + Knowledge Graph",
        "3. Validate Titleblock Fields",
        "4. Run Full Pipeline with Validation"
    ]
    pipeline_choice = choose_option(pipeline_options)

    start_time = time.time()

    if pipeline_choice.startswith("1"):
        pipeline = LayoutExtractionPipeline()
        pipeline.process(input_pdf_path, output_dir)

    elif pipeline_choice.startswith("2"):
        layout_proc = PDFLayoutProcessor(output_dir, isofields_path, rdl_ttl_path)
        layout_proc.run()

    elif pipeline_choice.startswith("3"):
        enriched_xml_path = find_enriched_xml(output_dir)
        print(f"\nRunning Validator on: {enriched_xml_path}")
        validator = Validator(enriched_xml_path, isofields_path)
        validator.validate_titleblock_fields()
        validator.print_report()

    elif pipeline_choice.startswith("4"):
        print(f"\n[1/3] Extracting structure from: {input_pdf_path}")
        pipeline = LayoutExtractionPipeline(debug=args.debug, debug_dir=args.debug_dir)
        pipeline.process(input_pdf_path, output_dir)

        print(f"\n[2/3] Running annotation and enrichment on: {output_dir}")
        layout_proc = PDFLayoutProcessor(output_dir, isofields_path, rdl_ttl_path)
        layout_proc.run()

        enriched_xml_path = find_enriched_xml(output_dir)
        print(f"\n[3/3] Running Validator on: {enriched_xml_path}")
        validator = Validator(enriched_xml_path, isofields_path)
        validator.validate_titleblock_fields()
        validator.print_report()
        validator.write_json_report()

    elapsed_time = time.time() - start_time
    print(f"\nPipeline completed in {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    main()
