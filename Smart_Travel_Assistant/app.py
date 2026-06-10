import os
import json
from flask import Flask, render_template, request, jsonify
from itinerary_generator import generate_itinerary, format_itinerary_text

# 创建Flask 应用对象
app = Flask(__name__)
# 设置密钥，作用：防止跨站请求伪造攻击
app.config["SECRET_KEY"] = os.urandom(24)

# 设置路由，处理用户请求
@app.route("/")
def index():
    # 返回HTML模板
    return render_template("index.html")

# 创建一个POST请求处理函数
@app.route("/generate", methods=["POST"])
def generate():
    # 获取POST请求的JSON数据
    data = request.get_json()
    # 获取用户的输入 -- 目的地、出行天数、偏好标签
    destination = data.get("destination", "").strip()
    days = data.get("days", 3)
    preferences = data.get("preferences", [])

    if not destination:
        return jsonify({"success": False, "error": "请输入目的地"})
    if not isinstance(days, int) or days < 1 or days > 30:
        return jsonify({"success": False, "error": "出行天数请设置在 1-30 天之间"})

    try:
        it_data = generate_itinerary(destination, days, preferences)
        if "error" in it_data:
            return jsonify({"success": False, "error": it_data["error"]})
        return jsonify({
            "success": True,
            "itinerary_text": format_itinerary_text(it_data),
            "itinerary_data": it_data
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"生成行程时出错: {str(e)}"})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)