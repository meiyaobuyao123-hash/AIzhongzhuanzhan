# Prism Gateway · Backend (v0.1)

透明定价的 AI 模型聚合网关。**采购成本 = 客户成本**，0% 加价，0.05% 充值手续费。

完整方案见 [`docs/v0.1-implementation-plan.md`](../docs/v0.1-implementation-plan.md)。

---

## 快速开始

### 本地开发

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 配置环境
cp .env.example .env
# 生成 master key 并写入 .env
echo "PRISM_MASTER_KEY_HEX=$(openssl rand -hex 32)" >> .env

# 初始化 DB（创建表 + 种子模型 catalog）
python -m scripts.init_db

# 启动开发服务器
uvicorn app.main:app --reload --host 127.0.0.1 --port 8765
```

### Admin 操作

```bash
# 创建测试用户
prism-admin user create --email dev@example.com

# 给用户充值（先建 admin 操作）
prism-admin user topup --id 1 --amount 100

# 创建 Prism Key
prism-admin key create --user-id 1 --name "Local laptop"
# → 输出 sk-prism-xxx... （仅此一次显示，后面只能看 prefix + last4）

# 添加上游 channel（用户给 Anthropic API Key 后）
prism-admin channel add \
  --provider anthropic \
  --name "Anthropic personal #1" \
  --base-url https://api.anthropic.com \
  --upstream-key "sk-ant-api03-..." \
  --models claude-opus-4-5,claude-sonnet-4-5,claude-haiku-4-5

# 查看用量
prism-admin usage stats --user-id 1 --since 2026-05-01
```

### 测试

```bash
pytest                    # 全部
pytest -k auth            # 只跑 auth 相关
pytest --cov=app          # 含覆盖率
```

---

## 设计原则

1. **0% 加价**：单价表 = 上游成本表
2. **N:M 共享池**：客户 Prism Key → 路由器 → 共享上游 Key 池
3. **OpenAI 协议优先**：`/v1/chat/completions` 是默认对外契约
4. **流式优先**：所有 LLM 默认走 SSE
5. **micro-cents 整数运算**：金钱永不浮点
6. **测试不依赖真实 Key**：respx mock httpx，95% 测试可本地跑

---

## 目录速查

```
app/            # FastAPI 应用
  main.py            # app 装配 + middleware
  config.py          # 环境变量
  db.py              # async session
  auth.py            # Prism Key 鉴权
  crypto.py          # AES-256-GCM 加解密上游 Key
  errors.py          # 错误码标准化（OpenAI 风格）
  models/orm.py      # 7 张表
  schemas/           # 请求/响应 pydantic 模型
  providers/         # anthropic / openai / google 适配器
  routes/            # 端点
  routing/           # 路由器
  billing/           # usage 提取 + 成本计算
  streaming/         # SSE pump

scripts/        # CLI 工具
  init_db.py         # 初始化数据库 + 种子 catalog
  prism_admin.py     # 管理员命令

tests/          # 单元测试 + e2e（用 respx mock 上游）

deploy/         # 部署配置
  prism.service          # systemd unit
  nginx-suanli-api.conf  # nginx /suanli-api/ location
```

---

## 部署

详见 [`docs/v0.1-implementation-plan.md`](../docs/v0.1-implementation-plan.md) §8。
