# caseplay

基于 Vue、Flask 与 MySQL 的法治教育互动剧本平台，支持 AI 主持、NPC 对话、分支选择与结局学习报告。

## npm 快速安装部署（推荐）

需要 Node.js 20+、已启动的 Docker 和 Docker Compose。无需单独安装 Python 或 MySQL。

当前可直接从 GitHub 安装：

```sh
npm install -g github:caseplay/caseplay
caseplay init mycaseplay
cd mycaseplay
caseplay config
caseplay config --mail
caseplay up
```

`config` 交互选择 Gemini、OpenAI、DeepSeek、通义千问或自定义兼容接口，API Key 输入不回显。`config --mail` 配置 QQ 邮箱与 SMTP 授权码，注册验证码功能需要此配置。打开 http://localhost:8080 。首次启动需要联网下载基础镜像及依赖。

无需全局安装也可执行：

```sh
npx --yes --package=github:caseplay/caseplay caseplay init mycaseplay
npx --yes --package=github:caseplay/caseplay caseplay config --dir mycaseplay
npx --yes --package=github:caseplay/caseplay caseplay up --dir mycaseplay
```

指定平台或自定义接口：

```sh
caseplay config --provider deepseek
caseplay config --provider custom --model your-model --base-url https://your-gateway.example/v1
caseplay up
caseplay status
caseplay logs
caseplay down
```

数据库镜像默认使用 MySQL 8.4，也可在 `.env` 中设置 `MYSQL_IMAGE=mysql:8.0` 使用兼容的 MySQL 8.0 镜像。

如本机 8080 端口已被占用，可在部署目录的 `.env` 设置 `CASEPLAY_PORT=8081` 后启动。

重新运行 `config` 可切换平台；切换时清除上一平台的模型和接口覆盖配置。各平台专用密钥分别保存。密钥仅保存在部署目录的 `.env` 中，Unix 系统权限设为 600，并自动加入 Git 忽略列表。请保管该目录。自动化场景可从安全的环境变量 `CASEPLAY_API_KEY` 读取密钥，配合 `--provider` 使用，避免把密钥直接写入命令参数。

`init` 自动生成数据库随机密码，拒绝覆盖已存在的目录。`down` 保留数据库卷。已有数据库卷不会因修改 `.env` 自动更新密码；请保留原数据库密码。已有旧数据库还需补齐 sessions 表的 status 和 end_report 字段，新部署自动创建。

### 发布到 npm

仓库已包含 npm 包配置和发布前测试。维护者使用有发布权限的 npm 账号执行：

```sh
npm login
npm publish --access public
```

成功发布且包名可用后，用户可以改用 `npm install -g caseplay` 或 `npx caseplay`。目前尚未发布到 npm registry，GitHub 安装命令可先使用。

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
