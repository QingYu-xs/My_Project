# 📄 墨问 AI - 智能文档问答助手 (Smart Doc Q&A)

基于 RAG（Retrieval-Augmented Generation）架构的智能文档问答系统。上传 PDF、Word、Markdown 或 TXT 文档后，即可基于文档内容进行自然语言问答，无需本地大模型，通过 API 调用即可运行。

## ✨ 项目亮点

- 🧠 **RAG 架构**：基于 LangChain 搭建完整检索增强生成链路，文档分块 → 向量化 → 语义检索 → LLM 生成
- 🔍 **FAISS 向量检索引擎**：使用 FAISS（Facebook AI Similarity Search）进行高效语义检索，索引持久化到磁盘，重启不丢失
- 🔌 **多模型兼容**：封装 OpenAI Compatible API，支持通义千问、智谱、DeepSeek 等任意兼容模型一键切换
- 📂 **多格式文档解析**：支持 PDF、Word（.docx）、Markdown（.md）、TXT 四种格式
- 🛡️ **MD5 文件去重**：上传时自动计算文件哈希值，重复文件自动跳过，避免重复计算浪费资源
- 💾 **文件列表持久化**：通过 JSON 注册表记录上传文件的历史信息，服务重启后侧边栏文件列表自动恢复
- 🎨 **交互式 Web 界面**：Flask 提供纯 JSON API，前端异步交互，拖拽上传 + Enter 快捷发送

## 📁 项目结构

```
Smart_Document_Q&A_Assistant/
├── app.py                        # Flask Web 应用主入口，定义全部路由
├── config/
│   └── settings.py               # 全局配置（API Key、模型参数、分块策略）
├── models/
│   ├── llm_factory.py            # Embedding / LLM 工厂，按 API 类型创建实例
│   └── qwen_embedding.py         # 通义千问 Embedding 适配器（解决 Dashscope 格式不兼容）
├── services/
│   ├── rag_service.py            # RAG 编排核心（上传→索引→检索→生成）
│   ├── vector_store.py           # FAISS 向量存储管理（增/删/查/持久化）
│   ├── document_loader.py        # 文档加载与递归分块
│   ├── docx_loader.py            # .docx 纯标准库解析器（zipfile + XML）
│   └── file_registry.py          # 文件注册表（MD5 去重 + 原始文件名映射）
├── templates/
│   └── index.html                # Web 前端页面（聊天界面）
├── static/
│   └── style.css                 # 前端样式
├── upload/                       # 上传文件临时存储
├── faiss_index/                  # FAISS 索引 + 文件注册表持久化目录
├── .env                          # 环境变量配置（API Keys）
└── README.md                     # 项目文档
```

## 🚀 快速开始

### 环境要求
- Python 3.10+
- 网络连接（调用 Embedding / LLM API）
- API Key（通义千问 / 智谱 / DeepSeek）

### 安装依赖
```shell
pip install flask langchain langchain-community langchain-openai langchain-text-splitters faiss-cpu pypdf
```

> `python-docx` 为非必需依赖。如未安装，系统会自动使用内置的纯标准库 .docx 解析器（`zipfile` + `xml.etree.ElementTree`）。

### 配置环境变量（在 `.env` 文件中）
```text
Qwen_API_KEY=sk-your-api-key-here
BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen3.6-plus
```

### 启动服务
```shell
python app.py
```
然后打开浏览器访问 `http://localhost:5000`

---

## 📖 Web 界面使用说明

1. 打开 `http://localhost:5000`
2. 在左侧点击上传 PDF、Word、Markdown 或 TXT 文档（支持拖拽上传）
3. 文档自动处理后，侧边栏显示已上传文件列表和文档块数统计
4. 在输入框输入问题，按 Enter 或点击发送按钮
5. 系统从文档中检索相关片段，基于文档内容生成回答

### 功能特点

- **多格式支持**：上传 PDF、Word、Markdown、TXT，统一处理流程
- **实时进度反馈**：上传时显示进度条，问答时显示思考指示器
- **参考文档追溯**：回答末尾标注参考的文档来源
- **一键清空**：清空所有文档索引和对话记录
- **文档去重保护**：重复上传同一文档自动跳过，避免重复计算

## 🛠️ 核心技术

### 1. RAG 检索增强生成

```
用户提问
  ↓
Embedding API 将问题向量化
  ↓
FAISS 相似度检索 Top-4 相关文档块
  ↓
检索结果 + 原始问题 拼接为 Prompt
  ↓
LLM 基于文档内容生成回答
```

### 2. Embedding 兼容处理

通义千问 Dashscope 的 OpenAI-Compatible 端点在 Embedding 接口上存在输入格式差异。标准 `OpenAIEmbeddings` 发送 `{"input": ["文本1", "文本2"]}` 会被 API 拒绝。

解决方案：手写 `QwenEmbeddings` 适配器，逐条调用 API，每条文本发送 `{"input": "单条文本"}`，实现 `embed_documents()` 和 `embed_query()` 接口，对 FAISS 完全透明。

### 3. 递归字符分割

采用 `RecursiveCharacterTextSplitter`，按优先级依次尝试分割符：Markdown 标题 → 代码块 → 段落 → 句号 → 空格 → 字符级别，确保每个分块语义完整。

### 4. .docx 纯标准库解析

.docx 文件本质是 ZIP 压缩包，内部包含 XML。通过 `zipfile` 解压 + `xml.etree.ElementTree` 直接解析，无需安装 `python-docx`。

### 5. MD5 文件去重

上传前计算文件 MD5 哈希值，查询 `file_registry.json` 注册表。若已存在则返回 `"该文档已存在！"`，不执行重复嵌入计算，节省 API 调用成本。

### 6. FAISS 索引持久化

每次 `add_documents` 后自动保存索引到 `faiss_index/` 目录，应用启动时自动加载已有索引，避免重复处理历史文档。

## 🧪 测试与验证

### 启动 Web 应用
```shell
python app.py
# 打开 http://localhost:5000
```

### 验证接口
```shell
# 查看系统状态
curl http://localhost:5000/status

# 查看已上传文件列表
curl http://localhost:5000/files
```

## ⚙️ 配置切换

在 `config/settings.py` 中修改 `DEFAULT_API_TYPE` 即可切换不同的模型服务：

```python
DEFAULT_API_TYPE = "qwen"     # 通义千问（默认）
DEFAULT_API_TYPE = "zhipu"    # 智谱 GLM
DEFAULT_API_TYPE = "deepseek" # DeepSeek
```

## 📄 许可证
本项目仅供学习交流使用。

## 🙏 致谢
感谢以下开源项目的支持：
- [LangChain](https://www.langchain.com/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Flask](https://flask.palletsprojects.com/)
- [通义千问 Dashscope](https://dashscope.aliyun.com/)
