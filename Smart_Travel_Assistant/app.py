import os
from flask import Flask, render_template, request, jsonify
from itinerary_generator import generate_itinerary, format_itinerary_text

# 创建 Flask 应用
app = Flask(__name__)
# 设置密钥，用于 session 加密和 CSRF 保护
app.config["SECRET_KEY"] = os.urandom(24)


@app.route("/")
def index():
    """首页：返回行程规划的前端页面"""
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """核心接口：接收用户输入，返回生成的行程数据"""
    # 解析前端发来的 JSON 请求体
    data = request.get_json()
    destination = data.get("destination", "").strip()
    days = data.get("days", 3)
    preferences = data.get("preferences", [])

    # 参数校验
    if not destination:
        return jsonify({"success": False, "error": "请输入目的地"})
    if not isinstance(days, int) or days < 1 or days > 30:
        return jsonify({"success": False, "error": "出行天数请设置在 1-30 天之间"})

    try:
        # 调用行程生成器获取结构化行程数据
        it_data = generate_itinerary(destination, days, preferences)
        if "error" in it_data:
            return jsonify({"success": False, "error": it_data["error"]})
        # 返回成功结果：格式化文本 + 原始数据（供前端渲染）
        return jsonify({
            "success": True,
            "itinerary_text": format_itinerary_text(it_data),
            "itinerary_data": it_data
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"生成行程时出错: {str(e)}"})


@app.route("/health")
def health():
    """健康检查接口"""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # 启动 Flask 开发服务器
    app.run(host="0.0.0.0", port=5700, debug=False, threaded=True)

