"""
通义千问 Dashscope Embedding 适配器。
Dashscope 的 /compatible-mode/v1/embeddings 端点要求单条文本调用，
标准格式：{model: ..., input: 单条文本}
本类逐条调 API，避免批量格式被拒。
"""
import json
import urllib.request
import urllib.error
from urllib.error import HTTPError
from typing import List


class QwenEmbeddings:
    """针对通义千问 Dashscope 的 Embedding 适配器。
    
    主要解决：LangChain 的 OpenAIEmbeddings 发送列表格式 {input: [...]]}，
    但 通义千问的 Dashscope 接口不接受列表，必须一条文本调一次。
    """

    def __init__(self, api_key: str, model: str = "text-embedding-v4", base_url: str = None):
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url.rstrip("/") if base_url
                         else "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self._url = f"{self.base_url}/embeddings"    # Embedding API 地址

    def _call_api(self, text: str) -> List[float]:
        """对单条文本调用 Embedding API，返回向量"""
        payload = json.dumps({
            "model": self.model,
            "input": text  # 单条文本，非数组
        }).encode("utf-8")

        req = urllib.request.Request(
            self._url, data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        # Dashscope 返回格式符合 OpenAI 规范：data[0].embedding
        return result["data"][0]["embedding"]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """逐个 Embed 每条文本，收集所有向量返回"""
        # 过滤掉空字符串或纯空白文本，避免 API 报错
        texts = [t for t in texts if t and t.strip()]
        if not texts:
            return []

        vectors = []
        errors = []
        for t in texts:
            try:
                vec = self._call_api(t)
                vectors.append(vec)
            except HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                errors.append(f"  text[:50]={t[:50]!r} -> HTTP {e.code}: {body}")
            except Exception as e:
                errors.append(f"  text[:50]={t[:50]!r} -> {str(e)}")

        if errors and not vectors:
            # 全部失败才抛异常；部分成功则返回成功的那部分
            raise RuntimeError(
                "所有 Embedding 调用均失败:\n" + "\n".join(errors)
            )
        return vectors

    def embed_query(self, text: str) -> List[float]:
        """Embed 单条查询文本"""
        if not text or not text.strip():
            return []
        return self._call_api(text)

    def __call__(self, _input):
        """支持直接被调用（LangChain FAISS 内部可能 call embedding 对象）
        - str   -> embed_query
        - list  -> embed_documents
        """
        if isinstance(input, str):
            return self.embed_query(_input)
        return self.embed_documents(_input)
