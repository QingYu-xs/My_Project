import os

rag_content = '''"""
RAG orchestration service.
Coordinates document processing and Q&A.
"""
import os
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from services.document_loader import DocumentLoaderService
from services.vector_store import VectorStoreService
from services.docx_loader import get_docx_loader
from config.settings import Config


UPLOAD_DIR = Path(__file__).resolve().parent.parent / "upload"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """你是一个智能文档问答助手。请基于以下文档内容回答问题。
如果文档中没有相关信息，请直接告诉用户"文档中没有找到相关信息"，不要编造答案。

参考文档：
{context}

请用中文回答。"""

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{question}"),
])


class RAGService:
    """RAG 服务：处理文档上传、检索、问答"""

    def __init__(self):
        ollama_base_url = getattr(Config, "OLLAMA_BASE_URL", "http://localhost:11434")
        embedding_model = getattr(Config, "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        llm_model = getattr(Config, "OLLAMA_LLM_MODEL", "qwen2.5:7b")

        self.vector_store = VectorStoreService(
            embedding_model=embedding_model,
            ollama_base_url=ollama_base_url,
        )
        self.llm = ChatOllama(
            model=llm_model,
            base_url=ollama_base_url,
            temperature=0.7,
        )
        self.document_loader = DocumentLoaderService()
        self.chat_history = []

    def upload_file(self, file_path):
        """上传并处理单个文件。返回处理结果信息。"""
        file_path = str(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        if ext not in Config.SUPPORT_FILES_TYPES:
            return {"status": "error", "message": "不支持的文件格式: " + ext}

        try:
            if ext == ".docx":
                loader = get_docx_loader(file_path)
                documents = loader.load()
                if isinstance(documents, list) and len(documents) > 0 and isinstance(documents[0], dict):
                    documents = [
                        Document(page_content=d["page_content"], metadata=d.get("metadata", {}))
                        for d in documents
                    ]
            else:
                result = self.document_loader.load_document(file_path)
                documents = result[0] if isinstance(result, list) and len(result) > 0 else result

            chunks = self.document_loader.splitter.split_documents(documents)

            if not chunks:
                return {"status": "error", "message": "文件内容为空，无法处理"}

            self.vector_store.add_documents(chunks)

            filename = os.path.basename(file_path)
            return {
                "status": "success",
                "message": "文件 " + filename + " 已处理，共 " + str(len(chunks)) + " 个文本块",
                "chunks": len(chunks),
            }

        except Exception as e:
            return {"status": "error", "message": "处理文件失败: " + str(e)}

    def ask(self, question, k=4):
        """根据问题检索相关文档并生成回答。"""
        if not self.vector_store.has_documents():
            return {
                "status": "error",
                "answer": "请先上传文档，再进行提问。",
                "sources": [],
            }

        try:
            docs = self.vector_store.similarity_search(question, k=k)

            if not docs:
                return {
                    "status": "success",
                    "answer": "文档中没有找到相关信息。",
                    "sources": [],
                }

            context = "\\n\\n".join([doc.page_content for doc in docs])
            prompt = RAG_PROMPT.format_messages(context=context, question=question)
            response = self.llm.invoke(prompt)

            sources = []
            seen = set()
            for doc in docs:
                src = doc.metadata.get("source", "")
                if src and src not in seen:
                    seen.add(src)
                    sources.append(os.path.basename(src))

            answer = response.content if hasattr(response, "content") else str(response)

            self.chat_history.append({"role": "user", "content": question})
            self.chat_history.append({"role": "assistant", "content": answer})

            return {"status": "success", "answer": answer, "sources": sources}

        except Exception as e:
            return {"status": "error", "answer": "回答生成失败: " + str(e), "sources": []}

    def get_history(self):
        """获取对话历史。"""
        return self.chat_history

    def clear_history(self):
        """清除对话历史和向量库。"""
        self.chat_history = []
        self.vector_store.clear()
'''

with open('services/rag_service.py', 'w', encoding='utf-8') as f:
    f.write(rag_content)
print('rag_service.py rewritten OK')
