# caseplay

基于 Vue、Flask 与 MySQL 的法治教育互动剧本平台，支持 AI 主持、NPC 对话、分支选择与结局学习报告。

## Docker 快速部署

安装 Docker Compose 后，在项目根目录执行：

```sh
python3 lmt.py init
# 编辑 .env：填写模型密钥、数据库密码与邮件授权码
python3 lmt.py up
```

打开 http://localhost:8080 。首次启动自动初始化数据库；数据保存在 mysql_data 卷。停止执行 `python3 lmt.py down`，保留数据。数据库初始化脚本仅在空数据卷运行。

## 本地 CLI 部署

需要 Python 3.10+、Node.js 22 和已创建的 MySQL lmt 数据库：

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r LMT_Server/requirements.txt
python lmt.py init
# 编辑 .env
python lmt.py db-init
python lmt.py serve
```

另开终端进入 LMT_UI，执行 `npm ci` 和 `npm run dev`，访问终端显示的地址。开发代理自动转发 /api 到 5000 端口。

## 多平台 Agent 配置

当前 AI 主持 Agent 通过统一接口选择平台，并非多个自治 Agent 协同。

| AI_PROVIDER | 密钥变量 | 默认模型 |
| --- | --- | --- |
| gemini | GEMINI_API_KEY | gemini-2.5-flash |
| openai | OPENAI_API_KEY | gpt-4o-mini |
| deepseek | DEEPSEEK_API_KEY | deepseek-chat |
| qwen | QWEN_API_KEY | qwen-plus |

也可统一填写 AI_API_KEY。平台专用密钥优先；用 AI_MODEL 覆盖模型，用 AI_BASE_URL 指定兼容 Chat Completions 的网关。修改后重启服务。模型可用性以平台账号为准。邮件注册需要 MAIL_SENDER 和 MAIL_API_KEY（QQ 邮箱 SMTP 授权码）。密钥只由后端读取，不放入前端构建。

## 结题汇报可用表述

完成部署与模型接入工程化：提供统一命令行入口，支持环境初始化、数据库初始化、服务启动及容器启停；通过 Docker Compose 编排前端、后端与数据库，提供数据库持久化和启动依赖检查；统一接入 Gemini 及 OpenAI 兼容接口，允许配置 OpenAI、DeepSeek、通义千问与自定义模型服务，并将敏感配置迁移到环境变量。

验证边界：已通过 Python 语法检查及前端生产构建；Docker 镜像构建、真实模型调用和邮件发送需在配置有效凭据后验收。现有用户身份校验仍需进一步加固，当前适用于结题演示环境。
