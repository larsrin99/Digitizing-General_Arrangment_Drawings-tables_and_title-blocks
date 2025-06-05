# GAD Extractor 🚧 (Experimental Master's Thesis Code)

This repository contains a modular pipeline for extracting structured data from General Arrangement Drawings (GADs) in vector-based PDF format. The system parses engineering documents, detects layout elements (tables, title blocks, annotations), and converts them into structured XML and semantically enriched RDF based on the ISO 15926 Reference Data Library.

> ⚠️ **Status**: This project is an experimental prototype developed as part of a master's thesis at NTNU. It is under active development and may contain incomplete or non-generalized components.



## 🛠️ Architecture Overview

The pipeline is composed of the following modular stages:

### 1. `pdf_converter.py`
Converts PDF pages into XML format using `pdfminer`, preserving layout structure (textboxes, lines, curves).

### 2. `extraction_pipeline.py`
Coordinates all submodules for line/rectangle/text extraction and final structuring.

### 3. `line_extractor.py`
Parses `<line>` and `<curve>` elements, with options for filtering and normalization.

### 4. `intersection_finder.py`
Detects intersection points among lines to support rectangle construction.

### 5. `rectangle_detector.py`
Forms candidate table or titleblock rectangles from intersections.

### 6. `textbox_mapper.py`
Assigns each text element to the best-fitting rectangle based on geometric overlap.

### 7. `rectangle_merger.py`
Merges overlapping or semantically adjacent rectangles based on spatial heuristics.

### 8. `visualizer.py`
Generates debug plots showing detected lines, rectangles, and textboxes.

### 9. `rdf_builder.py`
Maps enriched XML content to an RDF graph aligned with ISO 15926 using `rdflib`.

---

## 🖼️ Implementation Figures



### 🧱 Layout Extraction Logic

![Layout Modules](gad-extractor/LayoutExtraction.drawio (7).png)


### ⛓️ Semantic Structuring Overview

![Pipeline Overview](gad-extractor/SemanticEnrichment.drawio (4).png)

---

## ⚠️ Known Limitations

- Rule-based logic may fail on **non-standard GADs** or degraded legacy scans.
- Layout detection is **sensitive to spacing**, causing misgroupings if tables/titleblocks are close together.
- Currently assumes **English-language field labels** and specific ISO 7200 placement patterns.
- AI modules for symbol recognition are **not yet integrated**, though planned.

---

## 🔭 Future Directions

- Integrate AI models (e.g., CNNs or Vision Transformers) for symbol detection.
- Expand semantic logic to handle spatial relationships and dimension lines.
- Build validation tools for quality checking extracted content.
- Generalize table detection to support multi-column and irregular table formats.

---

## 📂 Example



---

## 👨‍🎓 Author

Lars Kveberg Ringstad  
NTNU – Master's Thesis 2025  

---

## 📄 License

This repository is released under the MIT License. See `LICENSE` for details.

