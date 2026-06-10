import os

app_content = """
import os
import uuid
from pathlib import Path

from flask import Flask, render_template, request, jsonify

from config.settings import Config
from services.rag_service import RAGService, UPLOAD_DIR

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_UPLOAD_SIZE
app.secret_key = "smart-doc-qa-secret-key"

# 检查 Ollama 状态
def check_ollama():
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:11434/api/tags")
        resp = urllib.request.urlopen(req, timeout=2)
        import json
        data = json.loads(resp.read())
        models = [m["name"] for m in data.get("models", [])]
        return {"running": True, "models": models}
    except Exception:
        return {"running": False, "models": []}

ollama_status = check_ollama()
rag_service = RAGService() if ollama_status["running"] else None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if not ollama_status["running"]:
        return jsonify({"status": "error", "message": "Ollama 未运行，请先启动 Ollama 服务"})

    if "file" not in request.files:
        return jsonify({"status": "error", "message": "请选择文件"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "请选择文件"})

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in Config.SUPPORT_FILES_TYPES:
        return jsonify({"status": "error", "message": f"不支持的文件格式: {ext}"})

    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / filename
    file.save(str(file_path))

    result = rag_service.upload_file(str(file_path))
    return jsonify(result)


@app.route("/ask", methods=["POST"])
def ask():
    if not ollama_status["running"]:
        return jsonify({"status": "error", "answer": "Ollama 未运行，请先启动 Ollama 服务"})

    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"status": "error", "answer": "请输入问题"})

    result = rag_service.ask(question)
    return jsonify(result)


@app.route("/history", methods=["GET"])
def history():
    if not ollama_status["running"]:
        return jsonify({"history": []})
    return jsonify({"history": rag_service.get_history()})


@app.route("/clear", methods=["POST"])
def clear():
    if rag_service:
        rag_service.clear_history()
    return jsonify({"status": "success", "message": "已清除所有数据"})


@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "ollama_running": ollama_status["running"],
        "ollama_models": ollama_status["models"],
        "has_documents": rag_service.vector_store.has_documents() if rag_service else False,
        "document_count": rag_service.vector_store.document_count() if rag_service else 0,
    })


if __name__ == "__main__":
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    Path("faiss_index").mkdir(parents=True, exist_ok=True)
    Path("templates").mkdir(parents=True, exist_ok=True)
    Path("static").mkdir(parents=True, exist_ok=True)

    ollama_status = check_ollama()
    if ollama_status["running"]:
        print(f"✅ Ollama 已连接，可用模型: {ollama_status['models']}")
        rag_service = RAGService()
    else:
        print("⚠️  未检测到 Ollama 服务，请启动 Ollama 后使用")
        print("   下载安装: https://ollama.com")
        print("   启动后拉取模型: ollama pull nomic-embed-text && ollama pull qwen2.5:7b")

    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
    )
"""

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_content)
print('app.py updated OK')
