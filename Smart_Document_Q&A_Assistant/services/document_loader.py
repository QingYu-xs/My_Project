"""
文档加载服务 - 支持多种文件格式
"""
import os
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import Config


class DocumentLoaderService:
    """ 文档加载和分割服务 """

    def __init__(self, chunk_size=None, chunk_overlap=None):
        """
        初始化方法
        :param chunk_size:文档分块大小
        :param chunk_overlap: 分割后每个文档的重叠部分
        """
        self.chunk_size = chunk_size or Config.DOCUMENT_SIZE_CHUK
        self.chunk_overlap = chunk_overlap or Config.CHUNK_OVERLAP

        # 创建文档分割器
        self.splitter = RecursiveCharacterTextSplitter(
            separators=[
                # Markdown 标题（优先级最高）
                "\n# ", "\n## ", "\n### ", "\n#### ",
                # Markdown 代码块标记
                "\n```\n",
                # 段落和换行
                "\n\n",
                "\n",
                # 中英文标点
                "。", "．",
                ". ",
                "！", "!",
                "？", "?",
                "；", ";",
                "，", ",",
                # Markdown 列表
                "\n- ", "\n* ", "\n+ ",
                "\n1. ", "\n2. ", "\n3. ",
                # 空格（最后手段）
                " ",
                ""
            ],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True
        )

    def load_document(self, file_path: str) -> list:
        """
        加载单个文档
        :param file_path:文件路径
        :return: 返回
        """
        # 获取文件扩展名
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in Config.SUPPORT_FILES_TYPES:
            raise ValueError(f'不支持的文件格式：{file_extension}')

        try:
            loader = self.get_loader(file_path, file_extension)
            documents = loader.load()
            return [documents, file_extension]

        except Exception as e:
            raise Exception(f'加载文件 {file_path} 失败：{str(e)}')

    def get_loader(self, file_path: str, file_extension: str):
        """
        根据文件类型获取对应的加载器
        :param file_path: 文件路径
        :param file_extension: 文件后缀名
        :return: 返回文件类型对应的文档加载器
        """
        loaders = {
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.txt': lambda path: TextLoader(path, encoding='utf-8'),
            '.md': lambda path: TextLoader(path, encoding='utf-8')
        }
        loader_class = loaders.get(file_extension)
        # 判断是否可调用
        if callable(loader_class):
            return loader_class(file_path)
        # 返回文件类型对应的文档加载器
        return loader_class

    def load_multiple_documents(self, file_paths: List[str]) -> list:
        """
        加载多个文档
        :param file_paths: 文件路径列表
        :return: 所有文档的列表
        """
        all_documents = []
        for file_path in file_paths:
            docs = self.load_document(file_path)
            all_documents.extend(docs)
        return all_documents

    def spilt_documents(self, documents: List):
        """
        分割文档
        :param documents:文档列表
        :return: 分割后的文档片段列表
        """
        return self.splitter.split_documents(documents)

    def process_files(self, file_path: List[str]):
        """
        处理文件：加载并分割
        :param file_path: 文件路径列表
        :return: 分割后的文档片段列表
        """
        documents = self.load_multiple_documents(file_path)
        return self.spilt_documents(documents)


if __name__ == '__main__':
    load_serve = DocumentLoaderService()
    # 加载文档
    file_path = r'D:\Python_Project\My_Warehouse\Python_AI\大模型应用开发\Langchain\RAG检索增强生成\datas\论文.txt'
    res = load_serve.load_document(file_path=file_path)
    print(res)
    # 获取文档对应的加载器
    res1 = load_serve.get_loader(file_path=file_path, file_extension=res[-1])
    print(res1)
