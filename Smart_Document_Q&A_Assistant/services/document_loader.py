"""
Document loader service - supports PDF, DOCX, TXT, MD files.
"""
import os
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import Config
from services.docx_loader import get_docx_loader


class DocumentLoaderService:
    """Document loading and splitting service."""

    def __init__(self, chunk_size=None, chunk_overlap=None):
        self.chunk_size = chunk_size or Config.DOCUMENT_SIZE_CHUK
        self.chunk_overlap = chunk_overlap or Config.CHUNK_OVERLAP

        self.splitter = RecursiveCharacterTextSplitter(
            separators=[
                "\n# ", "\n## ", "\n### ", "\n#### ",
                "\n```\n",
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True,
        )

    def load_document(self, file_path: str) -> list:
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in Config.SUPPORT_FILES_TYPES:
            raise ValueError(f"Unsupported file format: {file_extension}")

        try:
            loader = self.get_loader(file_path, file_extension)
            documents = loader.load()
            return [documents, file_extension]
        except Exception as e:
            raise Exception(f"Failed to load {file_path}: {str(e)}")

    def get_loader(self, file_path: str, file_extension: str):
        loaders = {
            ".pdf": PyPDFLoader,
            ".docx": get_docx_loader,
            ".txt": lambda path: TextLoader(path, encoding="utf-8"),
            ".md": lambda path: TextLoader(path, encoding="utf-8"),
        }
        loader_class = loaders.get(file_extension)
        if callable(loader_class):
            return loader_class(file_path)
        return loader_class

    def load_multiple_documents(self, file_paths: List[str]) -> list:
        all_documents = []
        for file_path in file_paths:
            docs = self.load_document(file_path)
            all_documents.extend(docs)
        return all_documents

    def spilt_documents(self, documents: List):
        return self.splitter.split_documents(documents)
