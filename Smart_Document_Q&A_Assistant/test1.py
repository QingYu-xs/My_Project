"""
文档加载服务 - 支持多种文件格式
"""
import os
from typing import List
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.settings import Config


class DocumentLoaderService:
    """文档加载和分割服务"""

    def __init__(self, chunk_size=None, chunk_overlap=None):
        self.chunk_size = chunk_size or Config.DOCUMENT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or Config.DOCUMENT_CHUNK_OVERLAP

        self.splitter = RecursiveCharacterTextSplitter(
            separators=['。', '.', '\n\n', '\n'],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True
        )

    def load_document(self, file_path: str) -> List:
        """
        加载单个文档

        Args:
            file_path: 文件路径

        Returns:
            文档列表

        Raises:
            ValueError: 不支持的文件格式
            Exception: 加载失败
        """
        # 获取文件扩展名
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension not in Config.SUPPORTED_FILE_TYPES:
            raise ValueError(f"不支持的文件格式: {file_extension}")

        try:
            # 创建加载器
            loader = self._get_loader(file_path, file_extension)
            documents = loader.load()
            return documents
        except Exception as e:
            raise Exception(f"加载文件 {file_path} 失败: {str(e)}")

    def _get_loader(self, file_path: str, file_extension: str):
        """根据文件扩展名获取对应的加载器"""
        loaders = {
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.txt': lambda path: TextLoader(path, encoding='utf-8')
        }

        loader_class = loaders.get(file_extension)
        if callable(loader_class):
            return loader_class(file_path)
        return loader_class

    def load_multiple_documents(self, file_paths: List[str]) -> List:
        """
        加载多个文档

        Args:
            file_paths: 文件路径列表

        Returns:
            所有文档的列表
        """
        all_documents = []
        for file_path in file_paths:
            docs = self.load_document(file_path)
            all_documents.extend(docs)
        return all_documents

    def split_documents(self, documents: List):
        """
        分割文档

        Args:
            documents: 文档列表

        Returns:
            分割后的文档片段列表
        """
        return self.splitter.split_documents(documents)

    def process_files(self, file_paths: List[str]):
        """
        处理文件：加载并分割

        Args:
            file_paths: 文件路径列表

        Returns:
            分割后的文档片段列表
        """
        documents = self.load_multiple_documents(file_paths)
        return self.split_documents(documents)
