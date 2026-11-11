#!/usr/bin/env node
import {
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
  cpSync,
  chmodSync,
} from "node:fs";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { randomBytes } from "node:crypto";
import { spawnSync } from "node:child_process";
import { parseArgs } from "node:util";
import { createInterface } from "node:readline/promises";
import { emitKeypressEvents } from "node:readline";

const source = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    dir: { type: "string" },
    provider: { type: "string" },
    model: { type: "string" },
    "base-url": { type: "string" },
    mail: { type: "boolean" },
    help: { type: "boolean", short: "h" },
  },
});
const command = positionals[0];
const root = resolve(
  values.dir || (command === "init" ? positionals[1] || "caseplay" : "."),
);
const envPath = join(root, ".env");
const providers = ["gemini", "openai", "deepseek", "qwen", "custom"];

function load() {
  if (!existsSync(envPath))
    throw new Error("请先执行 caseplay init，再进入该目录。");
  return Object.fromEntries(
    readFileSync(envPath, "utf8")
      .split(/\r?\n/)
      .filter((l) => /^[A-Z_]+=/.test(l))
      .map((l) => {
        const i = l.indexOf("=");
        let v = l.slice(i + 1);
        if (v.startsWith('"') && v.endsWith('"')) v = JSON.parse(v);
        return [l.slice(0, i), v];
      }),
  );
}
function save(env) {
  for (const value of Object.values(env)) {
    if (/[\r\n\0]/.test(value)) throw new Error("配置不能包含换行符。");
  }
  writeFileSync(
    envPath,
    Object.entries(env)
      .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
      .join("\n") + "\n",
    { mode: 0o600 },
  );
  chmodSync(envPath, 0o600);
}
async function ask(prompt) {
  if (!process.stdin.isTTY)
    throw new Error(
      "需要交互终端；自动配置可使用 --provider 和 CASEPLAY_API_KEY 环境变量。",
    );
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  try {
    return (await rl.question(prompt)).trim();
  } finally {
    rl.close();
  }
}
async function secret(prompt) {
  if (!process.stdin.isTTY)
    throw new Error("请在交互终端输入密钥，或设置 CASEPLAY_API_KEY 环境变量。");
  process.stdout.write(prompt);
  emitKeypressEvents(process.stdin);
  process.stdin.setRawMode(true);
  process.stdin.resume();
  return new Promise((resolveSecret, reject) => {
    let value = "";
    function done(error) {
      process.stdin.removeListener("keypress", handler);
      process.stdin.setRawMode(false);
      process.stdin.pause();
      process.stdout.write("\n");
      if (error) reject(error);
      else resolveSecret(value);
    }
    function handler(str, key = {}) {
      if (key.ctrl && key.name === "c") return done(new Error("已取消。"));
      if (key.name === "return") return done();
      if (key.name === "backspace") value = value.slice(0, -1);
      else if (
        str &&
        !key.ctrl &&
        !key.meta &&
        !/[\r\n\x00-\x1f\x7f]/.test(str)
      )
        value += str;
    }
    process.stdin.on("keypress", handler);
  });
}
function docker(args) {
  const result = spawnSync(
    "docker",
    [
      "compose",
      "--project-directory",
      root,
      "--env-file",
      envPath,
      "-f",
      join(root, "compose.yaml"),
      ...args,
    ],
    { stdio: "inherit" },
  );
  if (result.error)
    throw new Error(
      "无法启动 Docker，请安装并启动 Docker Desktop / Docker Compose。",
    );
  if (result.status !== 0)
    throw new Error(`Docker 执行失败（${result.status}）。`);
}

try {
  if (values.help || !command) {
    console.log(
      `Caseplay\n\n  caseplay init [目录]   复制部署项目并生成数据库随机密码\n  caseplay config       交互配置模型平台和 API Key（隐藏输入）\n  caseplay config --mail 配置预留邮件服务\n  caseplay up           构建并启动 Docker 服务\n  caseplay down         停止服务，保留数据库\n  caseplay admin 邮箱   将已注册账号设为内容管理员\n  caseplay logs         查看日志\n  caseplay status       查看服务状态\n\n选项：--dir 目录 --provider 平台 --model 模型 --base-url 接口地址\n支持 gemini / openai / deepseek / qwen / custom。需要 Node.js 20+ 和 Docker Compose。`,
    );
  } else if (command === "admin") {
    const email = positionals[1];
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
      throw new Error(
        "请输入已注册账号的邮箱：caseplay admin user@example.com",
      );
    docker([
      "exec",
      "-T",
      "api",
      "python",
      "-c",
      'import sys; from main import app; from storage import User; from sqlalchemy import select; db=app.config["DB_FACTORY"](); u=db.scalar(select(User).where(User.email==sys.argv[1].lower())); assert u is not None, "Account must be registered first"; u.is_admin=True; db.commit(); db.close(); print("Content administrator enabled")',
      email,
    ]);
  } else if (command === "init") {
    if (existsSync(root))
      throw new Error("目标目录已存在，请选择新目录，避免覆盖文件。");
    mkdirSync(root, { recursive: true });
    for (const path of [
      "Dockerfile",
      "compose.yaml",
      "db_init.sql",
      ".dockerignore",
      ".env.example",
      "deploy",
      "config",
      "LMT_Server",
      "LMT_Script",
      "LMT_UI",
    ]) {
      cpSync(join(source, path), join(root, path), {
        recursive: true,
        filter: (p) =>
          ![
            "node_modules",
            "__pycache__",
            "dist",
            ".env",
            ".DS_Store",
          ].includes(p.split(/[\\/]/).pop()),
      });
    }
    writeFileSync(envPath, readFileSync(join(root, ".env.example")), {
      mode: 0o600,
    });
    const env = load();
    env.MYSQL_PASSWORD = randomBytes(24).toString("hex");
    env.MYSQL_ROOT_PASSWORD = randomBytes(24).toString("hex");
    save(env);
    writeFileSync(join(root, ".gitignore"), ".env\nnode_modules/\n");
    console.log(
      `已创建 ${root}\n进入该目录后执行 caseplay config，再执行 caseplay up。`,
    );
  } else if (command === "config") {
    const env = load();
    if (values.mail) {
      env.MAIL_SENDER = await ask("发件 QQ 邮箱：");
      const key = await secret("SMTP 授权码（隐藏输入）：");
      if (!key || !env.MAIL_SENDER) throw new Error("邮箱和授权码不能为空。");
      env.MAIL_API_KEY = key;
    } else {
      const provider =
        values.provider || (await ask(`模型平台 [${providers.join("/")}]：`));
      if (!providers.includes(provider)) throw new Error("不支持的平台。");
      const key =
        process.env.CASEPLAY_API_KEY || (await secret("API Key（隐藏输入）："));
      if (!key) throw new Error("API Key 不能为空。");
      env.AI_PROVIDER = provider;
      if (provider === "custom") env.AI_API_KEY = key;
      else env[`${provider.toUpperCase()}_API_KEY`] = key;
      delete env.AI_MODEL;
      delete env.AI_BASE_URL;
      if (values.model) env.AI_MODEL = values.model;
      if (values["base-url"]) env.AI_BASE_URL = values["base-url"];
      if (provider === "custom") {
        env.AI_MODEL ||= await ask("模型名称：");
        env.AI_BASE_URL ||= await ask("兼容接口地址（含 /v1）：");
        if (!env.AI_MODEL || !env.AI_BASE_URL)
          throw new Error("自定义平台需要模型和接口地址。");
      }
      if (env.AI_BASE_URL) {
        const url = new URL(env.AI_BASE_URL);
        if (
          !["http:", "https:"].includes(url.protocol) ||
          url.username ||
          url.password ||
          url.search ||
          url.hash
        )
          throw new Error(
            "接口地址必须是 HTTP(S) URL，不能包含凭据、查询参数或片段。",
          );
      }
    }
    save(env);
    console.log(
      "配置已保存到本地 .env，密钥不会显示。执行 caseplay up 应用配置。",
    );
  } else if (["up", "down", "logs", "status"].includes(command)) {
    const env = load();
    if (command === "up") {
      if (
        !env.AI_PROVIDER ||
        !(env[`${env.AI_PROVIDER.toUpperCase()}_API_KEY`] || env.AI_API_KEY)
      )
        throw new Error("请先执行 caseplay config 配置模型密钥。");
      docker(["up", "-d", "--build"]);
      console.log(
        `服务已启动：http://localhost:${env.CASEPLAY_PORT || "8080"}（首次构建可能需要数分钟）`,
      );
    } else
      docker(
        command === "logs"
          ? ["logs", "--tail", "100"]
          : command === "status"
            ? ["ps"]
            : ["down"],
      );
  } else throw new Error(`未知命令：${command}`);
} catch (error) {
  console.error(`Caseplay: ${error.message}`);
  process.exitCode = 1;
}
