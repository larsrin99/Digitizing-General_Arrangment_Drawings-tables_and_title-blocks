# GAD Extractor: Engineering Knowledge Extraction from General Arrangement Drawings

This repository hosts a modular, standards-aligned pipeline for extracting and semantically enriching metadata from General Arrangement Drawings (GADs). It is based on the Master’s thesis by **Lars Kveberg Ringstad** at NTNU.

---

## 🚀 Overview

The project converts unstructured vector-based PDF drawings into structured XML and RDF representations. It leverages standards such as:

- **ISO 15926** (Reference Data Library)
- **ISO 7200** (Title Block)
- **ISO 5457** (Drawing Frames)
- **ISO 128-1** (Technical Drawing Standards)

---

## 🧠 Features

- Rule-based title block and table extraction
- Vector-aware parsing using `pdfminer.six`
- Spatial layout inference and element classification
- ISO-compliant RDF output using `rdflib`
- Configurable metadata normalization via JSON
- Semantic validation with `pySHACL`

---

## 📁 Project Structure

```text
layout_extraction/
  - Handles visual layout processing and object detection

semantic_annotation/
  - Converts parsed data into a standards-compliant knowledge graph
