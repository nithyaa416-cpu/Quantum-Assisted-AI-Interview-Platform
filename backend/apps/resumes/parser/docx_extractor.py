"""
DOCX and DOC text extraction.
Supports:
1. Modern .docx (Office Open XML) using python-docx with zipfile+XML fallback (zero-dependency).
2. Legacy .doc (Word 97-2003 binary OLE format) with string extraction.
3. Plain text (.txt).
"""
import io
import os
import re
import logging
import zipfile
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# OpenXML namespaces
W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
XML_NAMESPACES = {'w': W_NS}


def _extract_from_docx_xml(file_path: str) -> str:
    """
    Extract text directly from .docx zip archive without external dependencies.
    Reads document.xml and any headers/footers to preserve contact info.
    """
    try:
        with zipfile.ZipFile(file_path, 'r') as docx_zip:
            namelist = docx_zip.namelist()
            parts_text = []

            # 1. Check header parts (often contains candidate name, email, phone, links)
            header_files = sorted([name for name in namelist if name.startswith('word/header') and name.endswith('.xml')])
            for hf in header_files:
                try:
                    xml_data = docx_zip.read(hf)
                    h_tree = ET.fromstring(xml_data)
                    for p in h_tree.iter(f'{{{W_NS}}}p'):
                        texts = [t.text for t in p.iter(f'{{{W_NS}}}t') if t.text]
                        if texts:
                            line = ''.join(texts).strip()
                            if line:
                                parts_text.append(line)
                except Exception as exc:
                    logger.debug('Skipping header %s: %s', hf, exc)

            # 2. Main document body (paragraphs and table cells are all <w:p>)
            if 'word/document.xml' in namelist:
                doc_xml = docx_zip.read('word/document.xml')
                doc_tree = ET.fromstring(doc_xml)
                for p in doc_tree.iter(f'{{{W_NS}}}p'):
                    texts = [t.text for t in p.iter(f'{{{W_NS}}}t') if t.text]
                    if texts:
                        line = ''.join(texts).strip()
                        if line:
                            parts_text.append(line)

            return '\n'.join(parts_text)

    except Exception as exc:
        logger.error('Failed to parse docx XML for %s: %s', file_path, exc)
        return ''


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from a .docx file.
    Tries python-docx first if installed, falls back to direct XML extraction.
    """
    # Try python-docx if installed
    try:
        import docx  # type: ignore
        doc = docx.Document(file_path)
        paragraphs = []

        # Read sections/header if present
        for section in doc.sections:
            if section.header:
                for hp in section.header.paragraphs:
                    text = hp.text.strip()
                    if text:
                        paragraphs.append(text)

        # Read main body paragraphs
        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                paragraphs.append(text)

        # Read tables (e.g. skills or education grids)
        for table in doc.tables:
            for row in table.rows:
                row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_texts:
                    # Deduplicate repeated merged cell text
                    deduped = []
                    for t in row_texts:
                        if not deduped or deduped[-1] != t:
                            deduped.append(t)
                    paragraphs.append(' | '.join(deduped))

        extracted = '\n'.join(paragraphs)
        if extracted.strip():
            return extracted
    except ImportError:
        pass
    except Exception as exc:
        logger.debug('python-docx failed for %s, falling back to XML: %s', file_path, exc)

    # Built-in XML extractor fallback (guaranteed to work without python-docx)
    return _extract_from_docx_xml(file_path)


def extract_text_from_doc(file_path: str) -> str:
    """
    Extract text from a legacy binary .doc file.
    Uses pattern matching to extract printable Unicode and ASCII strings.
    """
    try:
        with open(file_path, 'rb') as f:
            content = f.read()

        # Try utf-16le chunks (typical in Word binary format)
        try:
            # Word 97-2003 stores text in 16-bit unicode strings
            text_pieces = re.findall(rb'(?:[\x20-\x7e]\x00){3,}', content)
            if text_pieces:
                decoded = [p.decode('utf-16le', errors='ignore').strip() for p in text_pieces]
                joined = '\n'.join(d for d in decoded if len(d) > 2)
                if len(joined) > 50:
                    return joined
        except Exception:
            pass

        # Fallback: extract ASCII sequences
        ascii_pieces = re.findall(rb'[\x20-\x7e\t\r\n]{4,}', content)
        if ascii_pieces:
            lines = [p.decode('ascii', errors='ignore').strip() for p in ascii_pieces]
            return '\n'.join(l for l in lines if len(l) > 2)

        return ''
    except Exception as exc:
        logger.error('Failed to extract text from .doc file %s: %s', file_path, exc)
        return ''
