"""
RAG 编排服务
协调 RAG 完整链路：文档上传 → 分块 → Embedding → FAISS 入库，
以及用户提问 → 语义检索 → Prompt 拼接 → LLM 生成回答。
"""
import os
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from services.document_loader import DocumentLoaderService
from services.vector_store import VectorStoreService
from services.file_registry import FileRegistry
from services.docx_loader import get_docx_loader
from models.llm_factory import LlmFactory
from config.settings import Config


# 上传文件存储目录
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "upload"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# Prompt 模板
# System Prompt：约束 LLM 仅基于给定文档上下文回答，
# 无相关信息时直接拒绝而非编造，降低幻觉率
SYSTEM_PROMPT = (
    "你是一个智能文档问答助手。请基于以下文档内容回答问题。\n"
    "如果文档中没有相关信息，请直接告诉用户'文档中没有找到相关信息'，不要编造答案。\n\n"
    "参考文档：\n{context}\n\n"
    "请用中文回答。"
)
RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{question}"),
])


class RAGService:
    """RAG 服务：文档上传 → 向量索引 → 检索增强问答"""

    def __init__(self, api_type=None):
        """初始化 Embedding、LLM、向量存储和文档加载器"""
        api_type = api_type or Config.DEFAULT_API_TYPE
        api_key = Config.get_api_key()

        self.embeddings = LlmFactory.create_embedding(
            api_type=api_type,
            api_key=os.environ.get("QWEN_API_KEY") or api_key,
        )
        self.llm = LlmFactory.create_llm(
            api_type=api_type,
            api_key=os.environ.get("QWEN_API_KEY") or api_key,
        )
        self.vector_store = VectorStoreService(embeddings=self.embeddings)
        self.document_loader = DocumentLoaderService()
        self.file_registry = FileRegistry()
        self.chat_history = []

    # 文件上传与索引入库
    def upload_file(self, file_path, original_name=None):
        """上传文件 → 分块 → Embedding → FAISS 入库"""
        file_path = str(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        # 校验文件格式
        if ext not in Config.SUPPORT_FILES_TYPES:
            return {"status": "error", "message": "不支持的文件格式: " + ext}

        # 计算文件 MD5，检查是否已存在
        md5_hash = FileRegistry.compute_md5(file_path)
        dup = self.file_registry.is_duplicate(md5_hash)
        if dup:
            return {"status": "skip", "message": f"该文档已存在！({dup})"}

        try:
            # Step 1: 根据文件类型选择加载器，提取文档文本
            if ext == ".docx":
                loader = get_docx_loader(file_path)          # 使用纯标准库解析器
                documents = loader.load()
                # 如果返回的是 dict 列表，转成 Document 对象
                if documents and isinstance(documents[0], dict):
                    documents = [
                        Document(page_content=d["page_content"], metadata=d.get("metadata", {}))
                        for d in documents
                    ]
            else:
                # PDF / TXT / MD 使用 LangChain 社区加载器
                result = self.document_loader.load_document(file_path)
                documents = result[0] if isinstance(result, list) and len(result) > 0 else result

            # Step 2: 递归分割为重叠文本块
            chunks = self.document_loader.splitter.split_documents(documents)
            if not chunks:
                return {"status": "error", "message": "文件内容为空，无法处理"}

            # 过滤掉空白内容的块，避免 Embedding API 报错
            chunks = [c for c in chunks if c.page_content and c.page_content.strip()]
            if not chunks:
                return {"status": "error", "message": "文件提取内容为空，无法处理"}

            # Step 3: Embedding 后加入 FAISS 索引
            self.vector_store.add_documents(chunks)

            filename = os.path.basename(file_path)
            # 注册文件到 registry
            uuid_key = os.path.basename(file_path)
            orig = original_name or uuid_key
            self.file_registry.register(uuid_key, orig, md5_hash)

            return {
                "status": "success",
                "message": f"文件 {orig} 已处理，共 {len(chunks)} 个文本块",
                "chunks": len(chunks),
                "uuid_name": uuid_key,
            }

        except Exception as e:
            return {"status": "error", "message": "处理文件失败: " + str(e)}

    # 问答
    def ask(self, question, k=4):
        """用户提问 → 语义检索 → 拼接上下文 → LLM 生成回答"""
        if not self.vector_store.has_documents():
            return {
                "status": "error",
                "answer": "请先上传文档，再进行提问。",
                "sources": [],
            }

        try:
            # Step 1: 从 FAISS 中检索最相似的 k 个文档块
            docs = self.vector_store.similarity_search(question, k=k)
            if not docs:
                return {
                    "status": "success",
                    "answer": "文档中没有找到相关信息。",
                    "sources": [],
                }

            # Step 2: 将检索结果拼接为上下文
            context = "\n\n".join([doc.page_content for doc in docs])
            prompt = RAG_PROMPT.format_messages(context=context, question=question)

            # Step 3: 调用 LLM 生成回答
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, "content") else str(response)

            # Step 4: 收集来源文件名（从注册表转为原始名称），供前端展示
            sources = list({
                self.file_registry.get_original_name(os.path.basename(doc.metadata.get("source", "")))
                for doc in docs if doc.metadata.get("source")
            })

            # 记录到对话历史
            self.chat_history.append({"role": "user", "content": question})
            self.chat_history.append({"role": "assistant", "content": answer})

            return {"status": "success", "answer": answer, "sources": sources}

        except Exception as e:
            return {"status": "error", "answer": "回答生成失败: " + str(e), "sources": []}

    def delete_file(self, uuid_name):
        file_path = str(os.path.join(str(UPLOAD_DIR), uuid_name))
        removed = self.vector_store.delete_by_source(file_path)
        self.file_registry.remove(uuid_name)
        disk_path = UPLOAD_DIR / uuid_name
        if disk_path.exists():
            disk_path.unlink()
        return removed

    def get_files(self):
        """返回已注册的文件列表 [(uuid, 原始名称), ...]"""
        return self.file_registry.get_all_files()

    def get_history(self):
        """返回当前会话的问答记录"""
        return self.chat_history

    def clear_history(self):
        """清空对话历史和 FAISS 索引"""
        self.chat_history = []
        self.vector_store.clear()
