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

### 🧠 Ontology

The ontology used in this project is defined in [`schema.ttl`](schema.ttl), and it serves as the semantic backbone for structuring extracted knowledge from General Arrangement Drawings (GADs).

This ontology was developed in alignment with the principles and terminology of:

- **ISO 10209** — *Vocabulary for terms relating to technical product documentation*
- **ISO 15926** — *Integration of lifecycle data for process plants including oil and gas production facilities*
- **ISO 15296** — *Industrial automation systems and integration — Generic reference architecture*

The ontology provides a formal vocabulary for key concepts such as:

- **Document structure**: title blocks, tables, rows, columns  
- **Engineering properties**: tag numbers, revision identifiers, dates, component types  
- **Spatial and layout relationships**: positions, bounding boxes, and containment

By linking extracted elements (from tables, annotations, and title blocks) to these ontology classes and properties, the pipeline supports machine-readable, standards-aligned knowledge graphs. These can be exported in RDF and queried using SPARQL to enable integration into broader data ecosystems such as digital twins, asset management systems, or data lakes.

> ℹ️ This ontology-driven enrichment ensures that the extracted content is not just structured, but also semantically interoperable, facilitating lifecycle data reuse and traceability across systems and projects.

---
## 🖼️ Implementation Figures



### 🧱 Layout Extraction Logic

![Layout Modules](gad-extractor/LayoutExtraction.png)


### ⛓️ Semantic Structuring Overview

![Pipeline Overview](gad-extractor/SemanticEnrichment.png)

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

