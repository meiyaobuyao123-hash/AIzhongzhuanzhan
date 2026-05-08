# Prism · 项目记忆（CLAUDE.md）

> 给任何在这个仓库工作的 Claude / agent 看的"项目北极星"。读完这一份你能继续干活。

---

## 0. 一句话定义

**Prism**：透明定价的 AI 模型聚合 API 网关。把 200+ 主流模型背后的 60+ 上游渠道汇聚成一个 OpenAI 兼容 API，按上游成本（**0% 加价**）+ 充值万 5（0.05%）手续费销售。

主域名：**https://www.ai100trading.cn/suanli/**（首页 + Web 控制台 + API 都在这个域）。

---

## 1. 已锁定决策（不要再讨论）

| # | 决策 | 不变量 |
|---|---|---|
| 1 | **API only，永不账号切片** | 不偷 Pro/Max OAuth token；只走开发者 API 账号 |
| 2 | **0% 加价 + 万 5 充值手续费** | inference 单价 = 上游单价；充 10000 到账 9995 |
| 3 | **2 档用户**：Self-serve / Team | 不要 Free / Developer 这种细分；self-serve 内部按累计充值阶梯做运行时差异化 |
| 4 | **渠道明牌** | 客户在请求详情面板能看到走的哪条 channel + region + 政策 |
| 5 | **micro-cents 整数运算** | 所有金钱数字以微分整数存储；杜绝浮点 |
| 6 | **6 种支付通道** | 支付宝 / 微信 / USDT (TRC20/SOL/EVM) / 对公 / Stripe；TRC20 是国内首选 |

USDT 收款地址（公开 - 已展示在首页）：
- **TRC20** (Tron, 国内首选): `TT24g41HLptouzxGycZxQKmWaTENK4K4HG`
- **Solana** (SPL): `66p5tnV6Fd7x5QmRE6X772PMVmVUVgozRzATJ4Ns9iQn`
- **EVM** (BSC/Polygon/Arbitrum/ERC20): `0xC862ff9Fd79D180950E546DBB8b108d5c9c38582`

---

## 2. 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Python 3.10+ / FastAPI / SQLAlchemy 2.0 async / aiosqlite (MVP) → asyncpg (Y1) |
| 流式 HTTP | httpx async + 自写 SSE pump |
| 前端 | 静态 HTML + React 18 via CDN + Babel standalone（**不用 build tooling**）|
| 部署 | systemd + nginx 反代，腾讯云轻量新加坡 (43.156.207.26, ubuntu) |
| Redis | 已安装在 :6379；用于限速 / 熔断 / OAuth state / cache 粘性 (v0.3) |
| HTTPS | Let's Encrypt 通过 certbot；当前仅 www. 证书有效，apex 没 A 记录 |

---

## 3. 文件地图

```
/Users/wenruiwei/Desktop/AIzhongzhuanzhan/         （本地开发）
├── docs/                               ← 所有产品/技术设计文档
│   ├── prd.md                          v0.1 PRD
│   ├── routing-strategy.md             路由策略（v0.1 单 channel + v0.3+ 4 层目标态）
│   ├── token-accounting.md             token 计费准确性 + 对账承诺
│   ├── payment-methods.md              6 种通道 + 收款地址 + SOP
│   ├── upstream-onboarding.md          上游接入操作手册（Anthropic 手动 / OpenAI 半自动 ...）
│   ├── competitor-analysis.md          18 家竞品调研
│   ├── v0.1-implementation-plan.md     v0.1 后端 MVP 实施方案
│   ├── v0.2-spec.md                    v0.2 全栈方案（auth/console/multi-channel/translator）
│   ├── v0.3-spec.md                    v0.3 (在做) 支付自动化 / 价格²反比 / cache 粘性 / 邀请返佣
│   └── oauth-setup.md                  OAuth 配置 walkthrough
│
├── backend/                            ← v0.1+v0.2 FastAPI 网关
│   ├── pyproject.toml                  依赖 + ruff/mypy/pytest 配置
│   ├── .env / .env.example             配置（.env 不入仓）
│   ├── app/
│   │   ├── main.py                     FastAPI app 装配 + lifespan
│   │   ├── config.py                   pydantic-settings
│   │   ├── db.py + models/orm.py       async SQLAlchemy
│   │   ├── auth.py                     Prism Key + argon2 + 鉴权
│   │   ├── jwt_auth.py                 JWT (HS256) + sessions
│   │   ├── crypto.py                   AES-256-GCM 加密上游 Key
│   │   ├── errors.py                   OpenAI 风格错误 + PrismException 子类
│   │   ├── limits.py                   Redis 限速 + 渠道熔断状态机
│   │   ├── audit.py                    audit_log + redact 敏感字段
│   │   ├── email.py                    SMTP (fallback 打日志)
│   │   ├── redis_client.py             单例
│   │   ├── oauth/                      GitHub + Google providers
│   │   ├── providers/                  anthropic / openai / google adapters
│   │   │   └── translators/            OAI ↔ Anthropic 协议互转 (v0.2 B5)
│   │   ├── routing/                    router (v0.2 多 channel) + executor (重试链)
│   │   ├── billing/                    pricing + recorder (扣费写日志)
│   │   ├── streaming/sse.py            SSE pump
│   │   └── routes/                     端点
│   │       ├── messages.py             POST /v1/messages (Anthropic 原生 + 翻译入口)
│   │       ├── chat.py                 POST /v1/chat/completions
│   │       ├── auth.py                 register / login / verify / change-pwd
│   │       ├── oauth.py                /auth/oauth/{provider}/{authorize,callback}
│   │       ├── account.py              /account/* 自助
│   │       ├── usage.py                /usage/* 含请求详情面板
│   │       ├── models.py               /v1/models
│   │       └── health.py               /healthz
│   ├── scripts/
│   │   ├── init_db.py                  建表 + 种子模型
│   │   ├── migrate_v01_to_v02.py       schema 迁移（idempotent）
│   │   └── prism_admin.py              Typer CLI: user/key/channel/model/payment/usage/audit/oauth
│   ├── deploy/
│   │   ├── prism.service               systemd unit
│   │   └── nginx-suanli-api.conf       nginx /suanli-api/ 反代
│   └── tests/                          pytest（145+ 用例，目标覆盖率 85%+）
│
├── site/                               ← 静态前端（首页 + 控制台 + signup/login）
│   ├── index.html                      首页（hero + features + pricing + payment 卡 + FAQ）
│   ├── signup.html / login.html        独立页
│   ├── console.html                    SPA（hash 路由 5 tabs）
│   ├── tokens.css / styles.css         设计系统（深色 + 渐彩 iridescent + 玻璃）
│   ├── auth-pages.css / console.css    页面专项
│   ├── api-client.js                   fetch + JWT
│   ├── hero.jsx / sections.jsx / app.jsx     首页组件
│   └── console-app.jsx                 控制台 5 tabs
│
└── prompts/                            Claude design 提示词包（早期产物，少用）
```

服务器目录：`/opt/prism/`（rsync 同步）+ `/var/www/suanli/`（前端静态）。

---

## 4. 服务器与 URL 速查

```
SSH:   ssh ubuntu@43.156.207.26   (.env 里 PRISM_MASTER_KEY_HEX 不要丢)
日志:  sudo journalctl -u prism -f
配置:  /opt/prism/.env             (chmod 600)
数据:  /opt/prism/data/prism.db    (SQLite)

公开 URL:
  /                             → Helix (其他业务，不动)
  /suanli/                      → Prism 静态首页
  /signup, /login, /console     → Prism Web (静态)
  /suanli-api/v1/...            → Prism API gateway (uvicorn :8765)
  /suanli-api/auth/...          → 鉴权
  /suanli-api/account/...       → 账户自助
  /suanli-api/usage/...         → 用量分析
```

---

## 5. 常用命令

### 本地

```bash
cd /Users/wenruiwei/Desktop/AIzhongzhuanzhan/backend
source .venv/bin/activate
pytest                              # 全部测试
pytest tests/test_auth_routes.py    # 单文件
ruff check app/ scripts/            # lint
mypy app/                           # 类型
```

### 服务器（先 ssh 进去）

```bash
cd /opt/prism
.venv/bin/prism-admin --help

# 用户
.venv/bin/prism-admin user create --email x@y.com
.venv/bin/prism-admin user topup --id 1 --amount 100
.venv/bin/prism-admin user list

# Key
.venv/bin/prism-admin key create --user-id 1 --name "..."
.venv/bin/prism-admin key list

# Channel (上游)
.venv/bin/prism-admin channel add --provider anthropic --base-url ... \
  --upstream-key sk-ant-... --models claude-opus-4-5,...
.venv/bin/prism-admin channel test --id 1
.venv/bin/prism-admin channel list

# OAuth
.venv/bin/prism-admin oauth set --provider github \
  --client-id Iv1.xxx --client-secret ghs_xxx
.venv/bin/prism-admin oauth status

# 用量 / 审计
.venv/bin/prism-admin usage stats --user-id 1 --since 2026-05-01
.venv/bin/prism-admin audit list --since 2026-05-01

# 服务
sudo systemctl restart prism
sudo systemctl status prism
sudo journalctl -u prism -f
```

### 部署（每次代码改动）

```bash
# 本地
git push origin main

# 服务器
cd /opt/prism
git pull   # 如果同步用 git；当前用 rsync 模式
# 或：从本地用 rsync (注意 --exclude='.env' --exclude='*.db'!)

cd /opt/prism
.venv/bin/pip install -e . --quiet
.venv/bin/python -m scripts.migrate_v01_to_v02   # 如果 schema 有变
sudo systemctl restart prism
```

⚠️ **重要陷阱**：rsync **不要**用 `--delete` 而不加 `--exclude='.env' --exclude='*.db'`，否则会把服务器上的 .env 和数据库删掉。

---

## 6. 不要做的事

| 不要 | 原因 |
|---|---|
| 给 inference 加价 | 永久承诺 0% 加价 |
| 在响应里改 token 数 | 直接照抄上游 usage 字段，对账依据 |
| 把上游 Key 明文落库或写日志 | crypto.py 加密；audit redact |
| 用浮点做金额 | 一律 micro-cents 整数 |
| 在 SDK / 客户端做 token 估算 | 服务端按上游 usage 字段精确计费 |
| 让前端跑 build tool | 静态 HTML + React via CDN，零 npm |
| 改现有 nginx 路径（/, /api/agent/, /tuning 等）| 不动其他业务的路由；仅在 server block 里**新增** location |
| 触碰订阅切片业务（买 Pro/Max 转售） | 长期归零风险，记忆污染，ToS 灰色 |

---

## 7. 提交规范

```
feat(backend-v0.X): stage BN — <短描述>

详细说明...

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

每个 stage 一个 commit。stage 名按 docs/v0.X-spec.md 里的字母编号。

---

## 8. 当前状态（更新于 2026-05-08）

- **v0.1**：✅ 已上线（commit `1e7cce8`）。骨架 + DB + admin CLI + 单 channel
- **v0.2**：✅ 全部 stage（B1-B6）已 commit + 部署。等用户给上游 Key 做 B7 联调验收
- **v0.3**：🚧 开发中。文档：`docs/v0.3-spec.md`

145+ 测试通过。Web 控制台已部署到 https://www.ai100trading.cn/console。

---

## 9. 用户偏好（与本项目主理人协作时的注意事项）

- **沟通**：中文。直接、不绕弯。不要把问题打包成多选项的 AskUserQuestion 一次问 4 个
- **节奏**：定下方向后"一气推到底"；不需要每个小节点都来确认；commit 后给"最终总结"即可
- **聊**：动手前要把 BLOCKING 决策聊清楚（底座选型 / 商业模式 / 范围）；琐碎的不用问
- **emoji**：除非他要求否则别用
- **代码** vs **文档**：每次重大改动都要更新 `docs/`；规范是"按版本切文件"——`v0.X-spec.md`
- **资源约束**：他手上目前只有个人 API 账号；近期会给真上游 Key
- **不要假设**：不存在的功能、不知道的细节，问而不要编

未来 Claude 在这个项目继续工作时，**先读 docs/{prd, v0.1-implementation-plan, v0.2-spec, v0.3-spec, routing-strategy, token-accounting, payment-methods}.md**，再看代码。
