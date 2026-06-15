"""
Flask 应用入口 — 定义路由、启动 Web 服务。
"""
import os
import uuid
from pathlib import Path

from flask import Flask, render_template, request, jsonify

from config.settings import Config
from services.rag_service import RAGService, UPLOAD_DIR

# Flask 应用初始化
app = Flask(__name__)
# 限制上传文件大小（由 Config 控制，默认 50MB）
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_UPLOAD_SIZE
app.secret_key = "smart-doc-qa-secret-key"

# 全局 RAG 服务实例（初始化时自动连接 API）
rag_service = RAGService()


# 路由：首页
@app.route("/")
def index():
    """渲染 Web 聊天界面"""
    return render_template("index.html")


# 路由：上传文档
@app.route("/upload", methods=["POST"])
def upload():
    """接收文件 → 保存到 upload 目录 → 交由 RAGService 处理"""
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "请选择文件"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "请选择文件"})

    # 校验文件扩展名
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in Config.SUPPORT_FILES_TYPES:
        return jsonify({"status": "error", "message": f"不支持的文件格式: {ext}"})

    # 用 UUID 重命名，避免文件名冲突
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / filename
    file.save(str(file_path))

    result = rag_service.upload_file(str(file_path), original_name=file.filename)
    return jsonify(result)


# 路由：提问
@app.route("/ask", methods=["POST"])
def ask():
    """接收问题 → RAG 检索 → 返回回答"""
    data = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"status": "error", "answer": "请输入问题"})

    result = rag_service.ask(question)
    return jsonify(result)


# 路由：对话历史
@app.route("/history", methods=["GET"])
def history():
    """返回当前会话的问答记录"""
    return jsonify({"history": rag_service.get_history()})


# 路由：清空数据
@app.route("/clear", methods=["POST"])
def clear():
    """清空对话历史和 FAISS 索引"""
    rag_service.clear_history()
    return jsonify({"status": "success", "message": "已清除所有数据"})


# 路由：系统状态
@app.route("/status", methods=["GET"])
def status():
    """返回向量库文档数量等状态信息，前端用来判断是否可以提问"""
    return jsonify({
        "has_documents": rag_service.vector_store.has_documents(),
        "document_count": rag_service.vector_store.document_count(),
    })

@app.route("/files", methods=["GET"])
def list_files():
    """返回已注册的文件列表（uuid名 + 原始名称），前端用于初始化文件列表"""
    return jsonify({"files": rag_service.get_files()})


@app.route("/delete", methods=["POST"])
def delete_file():
    data = request.get_json()
    uuid_name = data.get("uuid_name", "")
    if not uuid_name:
        return jsonify({"status": "error", "message": "参数缺失"})
    count = rag_service.delete_file(uuid_name)
    return jsonify({"status": "success", "message": f"已删除 {count} 个向量块", "removed": count})

@app.route("/favicon.ico")
def favicon():
    return "", 204


# 启动入口
if __name__ == "__main__":
    # 确保必要目录存在
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    Path("faiss_index").mkdir(parents=True, exist_ok=True)
    Path("templates").mkdir(parents=True, exist_ok=True)
    Path("static").mkdir(parents=True, exist_ok=True)

    print(f"\u2705 API: {Config.DEFAULT_API_TYPE}")
    print(f"   LLM: {Config.API_KEYS[Config.DEFAULT_API_TYPE]['llm_model']}")
    print(f"   Embedding: {Config.API_KEYS[Config.DEFAULT_API_TYPE]['embedding_model']}")
    print(f"   启动 Flask: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")  # type ignore

    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
    )
