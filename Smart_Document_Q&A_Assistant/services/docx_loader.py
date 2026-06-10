"""
Simple docx text extractor using only stdlib.
Falls back when python-docx is not available.
"""
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


class SimpleDocxLoader:
    """Extract plain text from .docx files using zipfile + XML parsing."""

    def __init__(self, file_path: str):
        self.file_path = str(file_path)

    def load(self):
        """Return list of LangChain-style Document objects."""
        try:
            from langchain_core.documents import Document
        except ImportError:
            Document = None

        text = self._extract_text()
        if Document is None:
            return [{"page_content": text, "metadata": {"source": self.file_path}}]
        return [Document(page_content=text, metadata={"source": self.file_path})]

    def _extract_text(self) -> str:
        """Extract plain text from a .docx file (which is a ZIP of XML)."""
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = []
        with zipfile.ZipFile(self.file_path) as z:
            xml_content = z.read("word/document.xml")
            root = ET.fromstring(xml_content)
            for para in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                texts = []
                for run in para.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r"):
                    for t in run.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
                        if t.text:
                            texts.append(t.text)
                if texts:
                    paragraphs.append("".join(texts))
        return "\n".join(paragraphs)


def get_docx_loader(file_path: str):
    """Return a docx loader using our stdlib-based SimpleDocxLoader."""
    return SimpleDocxLoader(file_path)
