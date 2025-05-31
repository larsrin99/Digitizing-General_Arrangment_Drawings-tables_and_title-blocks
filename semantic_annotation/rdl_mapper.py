from lxml import etree
import rdflib
from difflib import SequenceMatcher, get_close_matches

class RDLMapper:
    def __init__(self, ttl_path):
        self.ttl_path = ttl_path
        self.graph = rdflib.Graph()
        self.graph.parse(ttl_path, format="ttl")
        self.rdl_info = self._extract_rdl_info()

    def _extract_rdl_info(self):
        rdl_info = {}
        for s in self.graph.subjects():
            label = self.graph.value(s, rdflib.RDFS.label)
            if label:
                label_str = str(label).strip().upper()
                rdl_info[label_str] = {
                    "uri": str(s),
                    "comment": str(self.graph.value(s, rdflib.RDFS.comment)) if (s, rdflib.RDFS.comment, None) in self.graph else None,
                }
        return rdl_info

    def enrich(self, xml_input_path, xml_output_path):
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(xml_input_path, parser)
        root = tree.getroot()

        # Add xmlns:rdl if missing
        nsmap = root.nsmap.copy()
        if 'rdl' not in nsmap:
            nsmap['rdl'] = "https://posccaesar.org/15926-4/v4/reference-data-item/"
            new_root = etree.Element(root.tag, nsmap=nsmap)
            new_root[:] = root[:]
            for k, v in root.attrib.items():
                new_root.set(k, v)
            root = new_root
            tree._setroot(root)

        # Try document-level classification
        title_field = root.xpath(".//document_property[@id='document_title']")
        if title_field:
            title_text = title_field[0].text.strip().upper()
            tokens = title_text.split()
            ngrams = [" ".join(tokens[i:i+n]) for n in range(2, 6) for i in range(len(tokens)-n+1)]
            best_match = None
            best_score = 0
            for phrase in ngrams:
                for label in self.rdl_info:
                    score = SequenceMatcher(None, phrase, label).ratio()
                    if score > best_score and score > 0.8:
                        best_match = label
                        best_score = score
            if best_match:
                root.set("type", best_match)

        # Match each <text> or <header>
        text_elements = root.xpath(".//text | .//header")
        for text_elem in text_elements:
            if text_elem.text:
                label = text_elem.text.strip().upper()
                matches = get_close_matches(label, self.rdl_info.keys(), n=1, cutoff=0.9)
                if matches:
                    match = matches[0]
                    info = self.rdl_info[match]

                    label_elem = etree.Element("{https://posccaesar.org/15926-4/v4/reference-data-item/}label")
                    label_elem.text = match
                    text_elem.addnext(label_elem)

                    uri_elem = etree.Element("{https://posccaesar.org/15926-4/v4/reference-data-item/}uri")
                    uri_elem.text = info["uri"]
                    label_elem.addnext(uri_elem)

                    if info["comment"]:
                        comment_elem = etree.Element("{https://posccaesar.org/15926-4/v4/reference-data-item/}comment")
                        comment_elem.text = info["comment"]
                        uri_elem.addnext(comment_elem)

        # Propagate header labels to all data rows
        for table_elem in root.findall(".//table"):
            self.propagate_labels_from_header(table_elem)

        tree.write(xml_output_path, pretty_print=True, encoding="utf-8", xml_declaration=True)
        print(f"✨ Enriched with RDL: {xml_output_path}")

    def propagate_labels_from_header(self, table_elem):
        rows = table_elem.findall('row')
        if len(rows) < 2:
            return

        header_row = rows[0]
        label_map = []

        for col in header_row.findall('column'):
            label_elem = col.find('{*}label')
            uri_elem = col.find('{*}uri')
            label_map.append({
                'label': label_elem.text if label_elem is not None else None,
                'uri': uri_elem.text if uri_elem is not None else None
            })

        for row in rows[1:]:
            for idx, col in enumerate(row.findall('column')):
                if idx >= len(label_map):
                    continue
                meta = label_map[idx]
                if meta['label']:
                    label_elem = etree.Element("{https://posccaesar.org/15926-4/v4/reference-data-item/}label")
                    label_elem.text = meta['label']
                    col.append(label_elem)
                if meta['uri']:
                    uri_elem = etree.Element("{https://posccaesar.org/15926-4/v4/reference-data-item/}uri")
                    uri_elem.text = meta['uri']
                    col.append(uri_elem)
