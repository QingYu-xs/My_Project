"""
文档加载服务
支持 PDF / DOCX / TXT / MD 四种格式的文件加载，
并通过递归字符分割器将文档切分为重叠的文本块。
"""
import os
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import Config
from services.docx_loader import get_docx_loader


class DocumentLoaderService:
    """加载文件并分割为文本块"""

    def __init__(self, chunk_size=None, chunk_overlap=None):
        self.chunk_size = chunk_size or Config.DOCUMENT_SIZE_CHUK
        self.chunk_overlap = chunk_overlap or Config.CHUNK_OVERLAP

        # 递归字符分割器：按优先级依次尝试分隔符，直到块大小符合 chunk_size
        self.splitter = RecursiveCharacterTextSplitter(
            separators=[
                "\n# ", "\n## ", "\n### ", "\n#### ",   # Markdown 标题（最高优先级）
                "\n`\n",   # 代码块
                "\n\n",   # 段落
                "\n",   # 行
                ". ",  # 英文句号
                " ",   # 空格
                "",    # 字符级别（兜底）
            ],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True,   # 记录每个块在原文中的起始位置
        )

    def load_document(self, file_path: str) -> list:
        """加载单个文件，返回 [Document列表, 扩展名]"""
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in Config.SUPPORT_FILES_TYPES:
            raise ValueError(f"不支持的文件格式: {file_extension}")

        try:
            loader = self.get_loader(file_path, file_extension)
            documents = loader.load()
            return [documents, file_extension]
        except Exception as e:
            raise Exception(f"文件加载失败 {file_path}: {str(e)}")

    def get_loader(self, file_path: str, file_extension: str):
        """根据文件扩展名选择对应的加载器"""
        loaders = {
            ".pdf": PyPDFLoader,                   # 基于 pypdf
            ".docx": get_docx_loader,               # 自定义纯标准库解析器
            ".txt": lambda path: TextLoader(path, encoding="utf-8"),
            ".md": lambda path: TextLoader(path, encoding="utf-8"),
        }
        loader_class = loaders.get(file_extension)
        if callable(loader_class):
            return loader_class(file_path)
        return loader_class

    def load_multiple_documents(self, file_paths: List[str]) -> list:
        """批量加载多个文件"""
        all_docs = []
        for file_path in file_paths:
            docs = self.load_document(file_path)
            all_docs.extend(docs)
        return all_docs

    def spilt_documents(self, documents: List):
        """将文档列表分割为重叠的文本块"""
        return self.splitter.split_documents(documents)
