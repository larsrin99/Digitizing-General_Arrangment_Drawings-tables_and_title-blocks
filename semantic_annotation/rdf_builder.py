from lxml import etree
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS
import uuid
import os

# Namespaces
GAD = Namespace("http://industrialgraph.org/gad-schema#")
RDL = Namespace("http://rdl.posccaesar.org/")

class RDFBuilder:
    def __init__(self, schema_path="schema.ttl"):
        self.schema_path = schema_path
        self.graph = Graph()
        self.graph.bind("gad", GAD)
        self.graph.bind("rdl", RDL)
        self.graph.parse(self.schema_path, format="turtle")
        print(f"✅ Loaded schema from {self.schema_path}")

    def generate_uri(self, entity_type: str) -> URIRef:
        return URIRef(f"{GAD}{entity_type}_{uuid.uuid4().hex[:8]}")

    def generate_rdf_from_xml(self, pdf_name: str):
        input_dir = f"data/output/{pdf_name}/"

        enriched_files = [f for f in os.listdir(input_dir) if f.endswith("_enriched_output.xml")]
        if not enriched_files:
            raise FileNotFoundError(f"No enriched XML found in {input_dir}")
        
        xml_path = os.path.join(input_dir, enriched_files[0])
        output_path = os.path.join(input_dir, "output.ttl")

        tree = etree.parse(xml_path)
        root = tree.getroot()

        doc_uri = self.generate_uri("Document")
        self.graph.add((doc_uri, RDF.type, GAD.Document))

        # === Titleblock ===
        tb_el = root.find("titleblock")
        if tb_el is not None:
            tb_uri = self.generate_uri("TitleBlock")
            self.graph.add((doc_uri, GAD.hasTitleBlock, tb_uri))
            self.graph.add((tb_uri, RDF.type, GAD.TitleBlock))

            # Document metadata
            metadata = tb_el.find("document_metadata")
            if metadata is not None:
                for prop in metadata.findall("document_property"):
                    prop_uri = self.generate_uri("DocumentProperty")
                    self.graph.add((tb_uri, GAD.hasProperty, prop_uri))
                    self.graph.add((prop_uri, RDF.type, GAD.DocumentProperty))

                    prop_id = prop.attrib.get("id")
                    bbox = prop.attrib.get("bbox")
                    value = (prop.text or "").strip()

                    if prop_id:
                        self.graph.add((prop_uri, GAD.hasId, Literal(prop_id)))
                        self.graph.add((prop_uri, GAD.hasLabel, Literal(prop_id)))
                    if bbox:
                        self.graph.add((prop_uri, GAD.hasBoundingBox, Literal(bbox)))
                    if value:
                        self.graph.add((prop_uri, GAD.hasValue, Literal(value)))

            for cell in tb_el.findall("cell"):
                cell_uri = self.generate_uri("Cell")
                self.graph.add((tb_uri, GAD.hasCell, cell_uri))
                self.graph.add((cell_uri, RDF.type, GAD.Cell))
                self.graph.add((cell_uri, GAD.hasBoundingBox, Literal(cell.attrib["bbox"])))

                for text in cell.findall("text"):
                    text_uri = self.generate_uri("TextElement")
                    self.graph.add((cell_uri, GAD.hasText, text_uri))
                    self.graph.add((text_uri, RDF.type, GAD.TextElement))
                    self.graph.add((text_uri, RDFS.label, Literal(text.text.strip())))
                    self.graph.add((text_uri, GAD.hasBoundingBox, Literal(text.attrib["bbox"])))
                    rdl = text.find("rdl:uri", namespaces={"rdl": "https://posccaesar.org/15926-4/v4/reference-data-item/"})
                    if rdl is not None:
                        self.graph.add((text_uri, GAD.linkedToRDL, URIRef(rdl.text)))

            for rev_table in tb_el.findall("revision_table"):
                rev_uri = self.generate_uri("RevisionTable")
                self.graph.add((tb_uri, GAD.hasRevisionTable, rev_uri))
                self.graph.add((rev_uri, RDF.type, GAD.RevisionTable))
                self.graph.add((rev_uri, GAD.hasBoundingBox, Literal(rev_table.attrib["bbox"])))

                for row in rev_table.findall("row"):
                    row_id = row.attrib.get("id")
                    row_uri = URIRef(f"{GAD}{row_id}") if row_id else self.generate_uri("Row")
                    self.graph.add((rev_uri, GAD.hasRow, row_uri))
                    self.graph.add((row_uri, RDF.type, GAD.Row))
                    if row_id:
                        self.graph.add((row_uri, GAD.hasId, Literal(row_id)))

                    for col in row.findall("column"):
                        col_id = col.attrib.get("id")
                        col_uri = URIRef(f"{GAD}{col_id}") if col_id else self.generate_uri("Column")
                        self.graph.add((row_uri, GAD.hasColumn, col_uri))
                        self.graph.add((col_uri, RDF.type, GAD.Column))
                        if col_id:
                            self.graph.add((col_uri, GAD.hasId, Literal(col_id))) 

                        for text in col.findall("text"):
                            text_uri = self.generate_uri("TextElement")
                            self.graph.add((col_uri, GAD.hasText, text_uri))
                            self.graph.add((text_uri, RDF.type, GAD.TextElement))
                            self.graph.add((text_uri, RDFS.label, Literal(text.text.strip())))
                            self.graph.add((text_uri, GAD.hasBoundingBox, Literal(text.attrib["bbox"])))
                            rdl = text.find("rdl:uri", namespaces={"rdl": "https://posccaesar.org/15926-4/v4/reference-data-item/"})
                            if rdl is not None:
                                self.graph.add((text_uri, GAD.linkedToRDL, URIRef(rdl.text)))

        # === Tabular Section ===
        tabular = root.find("tabular_section")
        if tabular is not None:
            ts_uri = self.generate_uri("TabularSection")
            self.graph.add((doc_uri, GAD.hasTabularSection, ts_uri))
            self.graph.add((ts_uri, RDF.type, GAD.TabularSection))

            for table in tabular.findall("table"):
                table_id = table.attrib.get("id")
                table_uri = URIRef(f"{GAD}{table_id}") if table_id else self.generate_uri("Table")
                self.graph.add((ts_uri, GAD.hasTable, table_uri))
                self.graph.add((table_uri, RDF.type, GAD.Table))
                self.graph.add((table_uri, GAD.hasBoundingBox, Literal(table.attrib["bbox"])))
                if table_id:
                    self.graph.add((table_uri, GAD.hasId, Literal(table_id)))
                
                header_el = table.find("header")
                if header_el is not None:
                    header_uri = self.generate_uri("Header")
                    self.graph.add((table_uri, GAD.hasHeader, header_uri))
                    self.graph.add((header_uri, RDF.type, GAD.Header))
                    self.graph.add((header_uri, RDFS.label, Literal(header_el.text.strip())))
                    self.graph.add((header_uri, GAD.hasBoundingBox, Literal(header_el.attrib["bbox"])))
                    
                for row in table.findall("row"):
                    row_id = row.attrib.get("id")
                    row_uri = URIRef(f"{GAD}{row_id}") if row_id else self.generate_uri("Row")
                    self.graph.add((table_uri, GAD.hasRow, row_uri))
                    self.graph.add((row_uri, RDF.type, GAD.Row))
                    if row_id:
                        self.graph.add((row_uri, GAD.hasId, Literal(row_id)))

                    for col in row.findall("column"):
                        col_id = col.attrib.get("id")
                        col_uri = URIRef(f"{GAD}{col_id}") if col_id else self.generate_uri("Column")
                        self.graph.add((row_uri, GAD.hasColumn, col_uri))
                        self.graph.add((col_uri, RDF.type, GAD.Column))
                        if col_id:
                            self.graph.add((col_uri, GAD.hasId, Literal(col_id)))

                        for text in col.findall("text"):
                            text_uri = self.generate_uri("TextElement")
                            self.graph.add((col_uri, GAD.hasText, text_uri))
                            self.graph.add((text_uri, RDF.type, GAD.TextElement))
                            self.graph.add((text_uri, RDFS.label, Literal(text.text.strip())))
                            self.graph.add((text_uri, GAD.hasBoundingBox, Literal(text.attrib["bbox"])))
                            rdl = text.find("rdl:uri", namespaces={"rdl": "https://posccaesar.org/15926-4/v4/reference-data-item/"})
                            if rdl is not None:
                                self.graph.add((text_uri, GAD.linkedToRDL, URIRef(rdl.text)))
                                
                        # Attach RDL annotations directly to column if present
                        rdl_label_el = col.find("{https://posccaesar.org/15926-4/v4/reference-data-item/}label")
                        rdl_uri_el = col.find("{https://posccaesar.org/15926-4/v4/reference-data-item/}uri")

                        if rdl_label_el is not None and rdl_label_el.text:
                            self.graph.add((col_uri, GAD.hasRdlLabel, Literal(rdl_label_el.text.strip())))
                        if rdl_uri_el is not None and rdl_uri_el.text:
                            self.graph.add((col_uri, GAD.hasRdlUri, URIRef(rdl_uri_el.text.strip())))

        self.graph.serialize(destination=output_path, format="turtle")
        print(f"✅ Combined RDF+Schema written to: {output_path}")
