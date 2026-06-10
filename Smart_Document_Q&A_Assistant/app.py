import os
import uuid
from pathlib import Path

from flask import Flask, render_template, request, jsonify

from config.settings import Config
from services.rag_service import RAGService, UPLOAD_DIR

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_UPLOAD_SIZE
app.secret_key = "smart-doc-qa-secret-key"

rag_service = RAGService()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
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
    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"status": "error", "answer": "请输入问题"})

    result = rag_service.ask(question)
    return jsonify(result)


@app.route("/history", methods=["GET"])
def history():
    return jsonify({"history": rag_service.get_history()})


@app.route("/clear", methods=["POST"])
def clear():
    rag_service.clear_history()
    return jsonify({"status": "success", "message": "已清除所有数据"})


@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "has_documents": rag_service.vector_store.has_documents(),
        "document_count": rag_service.vector_store.document_count(),
    })


if __name__ == "__main__":
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    Path("faiss_index").mkdir(parents=True, exist_ok=True)
    Path("templates").mkdir(parents=True, exist_ok=True)
    Path("static").mkdir(parents=True, exist_ok=True)

    print(f"\u2705 API: {Config.DEFAULT_API_TYPE}")
    print(f"   LLM: {Config.API_KEYS[Config.DEFAULT_API_TYPE]['llm_model']}")
    print(f"   Embedding: {Config.API_KEYS[Config.DEFAULT_API_TYPE]['embedding_model']}")
    print(f"   启动 Flask: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")

    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
    )
