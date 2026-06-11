"""
FAISS 向量存储服务
管理 FAISS 索引的构建、持久化、检索和清除。
"""
from pathlib import Path

from langchain_community.vectorstores import FAISS


FAISS_INDEX_DIR = Path(__file__).resolve().parent.parent / "faiss_index"
"""FAISS 索引文件存储目录"""


class VectorStoreService:
    """FAISS 向量索引管理器"""

    def __init__(self, embeddings):
        self.embeddings = embeddings        # 外部注入的 Embedding 实例
        self.vector_store = None             # FAISS 索引对象（首次 add_documents 时创建）
        self._load_index()                    # 启动时尝试加载已有索引

    # 持久化
    def _load_index(self):
        """从磁盘加载已持久化的 FAISS 索引，避免重复处理历史文档"""
        index_file = FAISS_INDEX_DIR / "index.faiss"
        if index_file.exists():
            try:
                self.vector_store = FAISS.load_local(
                    str(FAISS_INDEX_DIR),
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
            except Exception:
                # 索引文件损坏或 embedding 不兼容时静默重建
                self.vector_store = None

    def save_index(self):
        """将 FAISS 索引保存到磁盘"""
        if self.vector_store is not None:
            self.vector_store.save_local(str(FAISS_INDEX_DIR))

    # 文档管理
    def add_documents(self, documents):
        """将文档 Embedding 后加入 FAISS 索引，并持久化"""
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
        else:
            self.vector_store.add_documents(documents)
        self.save_index()

    def similarity_search(self, query, k=4):
        """语义检索：返回与 query 最相似的 k 个文档块"""
        if self.vector_store is None:
            return []
        return self.vector_store.similarity_search(query, k=k)

    # 工具方法
    def clear(self):
        """清空索引并删除所有持久化文件"""
        self.vector_store = None
        if FAISS_INDEX_DIR.exists():
            for f in FAISS_INDEX_DIR.iterdir():
                f.unlink()

    def has_documents(self):
        """索引中是否有文档向量"""
        if self.vector_store is None:
            return False
        try:
            return self.vector_store.index.ntotal > 0
        except Exception:
            return False

    def document_count(self):
        """索引中的文档块数量"""
        if self.vector_store is None:
            return 0
        try:
            return self.vector_store.index.ntotal
        except Exception:
            return 0
