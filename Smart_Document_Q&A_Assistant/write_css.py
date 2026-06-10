import os

css = """/* ===== 全局样式 ===== */
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:#f0f2f5;color:#1a1a2e;height:100vh;overflow:hidden}
.container{display:flex;height:100vh;max-width:1400px;margin:0 auto;background:#fff;box-shadow:0 0 20px rgba(0,0,0,0.05)}

/* ===== 侧边栏 ===== */
.sidebar{width:300px;min-width:300px;background:#f8f9fc;border-right:1px solid #e8ecf1;display:flex;flex-direction:column;padding:20px}
.sidebar-header h2{font-size:18px;font-weight:600;color:#1a1a2e;margin-bottom:16px}
.upload-area{margin-bottom:20px}
.upload-box{border:2px dashed #d0d5dd;border-radius:8px;padding:20px;text-align:center;cursor:pointer;transition:all 0.2s;background:#fff}
.upload-box:hover,.upload-box.dragover{border-color:#4f6ef7;background:#f0f3ff}
.upload-icon{color:#98a2b3;margin-bottom:8px}
.upload-text{font-size:13px;color:#475467;margin-bottom:4px}
.upload-hint{font-size:11px;color:#98a2b3;margin-bottom:12px}
.upload-btn{background:#4f6ef7;color:#fff;border:none;padding:8px 20px;border-radius:6px;font-size:13px;cursor:pointer;transition:background 0.2s}
.upload-btn:hover{background:#3d5bd9}
.upload-progress{padding:20px}
.progress-bar{width:100%;height:6px;background:#e8ecf1;border-radius:3px;overflow:hidden;margin-bottom:8px}
.progress-fill{height:100%;background:#4f6ef7;border-radius:3px;transition:width 0.3s;width:0%}
.progress-text{font-size:12px;color:#98a2b3;text-align:center}
.file-list{flex:1;overflow-y:auto;margin-bottom:16px}
.file-list-header{display:flex;justify-content:space-between;align-items:center;font-size:13px;color:#475467;margin-bottom:8px;padding:0 4px}
.file-count{background:#e8ecf1;padding:2px 8px;border-radius:10px;font-size:11px;color:#475467}
.file-items{display:flex;flex-direction:column;gap:6px}
.file-item{display:flex;align-items:center;gap:10px;padding:8px 10px;background:#fff;border:1px solid #e8ecf1;border-radius:6px;font-size:13px}
.file-icon{color:#4f6ef7;flex-shrink:0}
.file-info{display:flex;flex-direction:column;min-width:0}
.file-name{color:#1a1a2e;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.file-chunks{font-size:11px;color:#98a2b3}
.sidebar-actions{padding-top:12px;border-top:1px solid #e8ecf1}
.action-btn{display:flex;align-items:center;gap:6px;width:100%;padding:8px 12px;background:#fff;border:1px solid #e8ecf1;border-radius:6px;font-size:13px;color:#475467;cursor:pointer;transition:all 0.2s}
.action-btn:hover{background:#fef2f2;border-color:#fca5a5;color:#dc2626}

/* ===== 主区域 ===== */
.main{flex:1;display:flex;flex-direction:column;position:relative}
.chat-header{padding:20px 24px;border-bottom:1px solid #e8ecf1;background:#fff}
.chat-header h1{font-size:20px;font-weight:600;color:#1a1a2e;margin-bottom:4px}
.chat-subtitle{font-size:13px;color:#98a2b3}

/* ===== 消息区域 ===== */
.chat-messages{flex:1;overflow-y:auto;padding:20px 24px;display:flex;flex-direction:column;gap:16px}
.message{display:flex;gap:12px;max-width:85%;animation:fadeIn 0.3s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.message.user{align-self:flex-end;flex-direction:row-reverse}
.message.welcome{align-self:flex-start}
.message-avatar{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.assistant-avatar{background:#eef2ff;color:#4f6ef7}
.user-avatar{background:#4f6ef7;color:#fff}
.message-content{background:#f8f9fc;padding:12px 16px;border-radius:12px;font-size:14px;line-height:1.6;color:#1a1a2e;white-space:pre-wrap;word-break:break-word}
.message.user .message-content{background:#4f6ef7;color:#fff}
.message.welcome .message-content{background:#f0f3ff;border:1px solid #e0e7ff}

/* ===== 输入区域 ===== */
.input-area{padding:16px 24px;border-top:1px solid #e8ecf1;background:#fff}
.input-wrapper{display:flex;gap:8px;align-items:flex-end;background:#f8f9fc;border:1px solid #e8ecf1;border-radius:10px;padding:8px;transition:border-color 0.2s}
.input-wrapper:focus-within{border-color:#4f6ef7}
.question-input{flex:1;border:none;background:transparent;padding:4px 8px;font-size:14px;line-height:1.5;color:#1a1a2e;resize:none;outline:none;font-family:inherit;max-height:120px}
.question-input::placeholder{color:#98a2b3}
.send-btn{width:36px;height:36px;border-radius:8px;border:none;background:#4f6ef7;color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s;flex-shrink:0}
.send-btn:hover:not(:disabled){background:#3d5bd9}
.send-btn:disabled{opacity:0.4;cursor:not-allowed}
.input-hint{margin-top:6px;font-size:11px;color:#98a2b3;padding-left:4px}

/* ===== 加载状态 ===== */
.loading-overlay{position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(255,255,255,0.85);display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:10}
.loading-spinner{width:36px;height:36px;border:3px solid #e8ecf1;border-top-color:#4f6ef7;border-radius:50%;animation:spin 0.8s linear infinite;margin-bottom:12px}
@keyframes spin{to{transform:rotate(360deg)}}
.loading-text{font-size:14px;color:#475467}

/* ===== 滚动条 ===== */
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:#d0d5dd;border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#98a2b3}

/* ===== 响应式 ===== */
@media(max-width:768px){.sidebar{display:none}.main{width:100%}.message{max-width:95%}}
"""

with open(os.path.join('static', 'style.css'), 'w', encoding='utf-8') as f:
    f.write(css)
print('CSS written OK')
