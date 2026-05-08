# Agent 协作指南（AGENTS.md）

> 给任何 AI agent（Claude / Codex / Cursor agent / Aider / etc.）看的"操作手册"。
> 项目背景见 [`CLAUDE.md`](CLAUDE.md)；产品方案见 `docs/`。

---

## 1. 开干前必读

按顺序读：

1. [`CLAUDE.md`](CLAUDE.md) —— 项目北极星 + 已锁决策 + 文件地图
2. [`docs/prd.md`](docs/prd.md) —— 商业模式 + 用户分层 + 边界
3. [`docs/v0.1-implementation-plan.md`](docs/v0.1-implementation-plan.md) —— 后端基础架构
4. [`docs/v0.2-spec.md`](docs/v0.2-spec.md) —— 当前已上线版本的能力范围
5. [`docs/v0.3-spec.md`](docs/v0.3-spec.md) —— 正在开发的版本
6. [`docs/routing-strategy.md`](docs/routing-strategy.md) —— 路由层设计
7. [`docs/token-accounting.md`](docs/token-accounting.md) —— 计费准确性原则

跳过这些直接看代码会迷路（项目跨多个 stage，命名规则不读 spec 不懂）。

---

## 2. 怎么跑起来

### 本地开发

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
echo "PRISM_MASTER_KEY_HEX=$(openssl rand -hex 32)" >> .env
echo "PRISM_JWT_SECRET=$(openssl rand -hex 32)" >> .env

python -m scripts.init_db          # 创表 + 种子模型
uvicorn app.main:app --reload      # 跑起来 :8765
```

### 测试

```bash
pytest                              # 全跑（145+ 测试）
pytest -k auth                      # 只跑 auth 模块
pytest tests/test_e2e_messages.py   # e2e 端到端
pytest --cov=app --cov-report=html  # 生成覆盖率报告
```

测试用 `respx` mock 上游 + `fakeredis` mock Redis，**完全不依赖外部服务**。

### Lint + 类型

```bash
ruff check app/ scripts/ tests/
ruff format app/ scripts/ tests/    # auto-format
mypy app/                           # 严格模式
```

---

## 3. 修改代码的工作流

### 3.1 小改（bugfix / typo / 单文件）

直接改、跑测试、commit。message 格式：

```
fix(<area>): <一句话描述>
```

### 3.2 大改（新模块 / 新 endpoint / schema 变更）

1. 先**更新对应的 spec 文件**（`docs/v0.X-spec.md`）—— 在相应 §下加描述
2. 写代码 + 测试
3. 测试通过
4. commit message 引用 spec 章节（例如 "stage B5 §5"）
5. 推到 main

### 3.3 跨 version 增量（v0.X → v0.X+1）

参考 v0.1→v0.2 的演进路径：
1. `docs/v0.X+1-spec.md` 描述完整 v0.X+1 实施方案
2. 分 stage 推（B1, B2, B3, ...）每个 stage 一次 commit
3. **数据库 schema 变更**必须同步更新：
   - `app/models/orm.py` 加字段
   - `scripts/migrate_v0X_to_v0X+1.py` 写迁移脚本（idempotent ALTER + create_all）
4. 部署到服务器先跑 migration 再 systemctl restart prism

---

## 4. 数据库 schema 不变量

**永远不要丢数据**。Migration 必须：
- ✅ idempotent（重复跑不报错）
- ✅ 用 `inspect()` 检测列是否已存在再 ALTER
- ✅ 默认值 + NOT NULL 同时给（否则 SQLite 加列失败）
- ❌ 不要 DROP COLUMN（SQLite 不支持，且数据会丢）
- ❌ 不要重命名列（同样问题）；要改名就 add_new + copy_data + 应用层切换 + drop_old（多步发布）

**金额字段**永远 BIGINT micro-cents：
- 1 USD = 100_000_000 micro-cents
- 不要 FLOAT / DECIMAL / NUMERIC

---

## 5. 测试规范

新模块必带测试。结构：

```
tests/
├── conftest.py                  # 共用 fixtures (db_session / fakeredis 自动 patch)
├── test_<module>.py             # 单元测试，按模块分文件
└── test_e2e_<flow>.py           # 端到端（FastAPI TestClient）
```

测试不能：
- 连真 Redis（用 fakeredis）
- 调真上游 API（用 respx mock）
- 写真文件系统外的文件（除非临时目录）
- 依赖网络

测试必须：
- 按行为命名：`test_user_disabled_returns_403` 不是 `test_user_1`
- 一个 test 只做一件事
- 用 `pytest.raises` 检查异常类型 + 消息片段
- 端到端测必须 patch `get_db` 用 in-memory engine

---

## 6. 部署到服务器

```bash
# 本地推 main → GitHub
git push

# rsync 到 /opt/prism（注意 exclude）
SSHPASS='...' sshpass -e rsync -avz --delete \
  --exclude='.venv' --exclude='__pycache__' \
  --exclude='.env' --exclude='*.db' --exclude='data/' \
  -e "ssh -o ..." \
  backend/ ubuntu@43.156.207.26:/opt/prism/

# 服务器上
ssh ubuntu@43.156.207.26 'cd /opt/prism && \
  .venv/bin/pip install -e . --quiet && \
  .venv/bin/python -m scripts.migrate_v0X_to_v0Y && \
  echo "..." | sudo -S systemctl restart prism'
```

⚠️ rsync `--delete` **必须** exclude `.env` 和 `*.db` 和 `data/`，否则一次部署清空线上数据。

### nginx 配置

仅**新增** location，**不动**现有的（`/`, `/api/agent/`, `/tuning` 等是其他业务）。
所有改动放 `/etc/nginx/snippets/nginx-*.conf`，然后通过 `include` 指令引入到 server block。

---

## 7. 上游 Key 安全

- 加密落库：`crypto.encrypt(plaintext, master_key)` → AES-256-GCM
- master_key 在 `.env` 的 `PRISM_MASTER_KEY_HEX`（32 字节 hex）
- 永远不出现在：日志 / audit_log / 错误响应 / git history
- 给运维查 channel 用 `prism-admin channel list`，只显示 prefix + last4

如果 master_key 丢了，所有上游 Key 都得重新输入。**备份 master_key 到密码管理器**。

---

## 8. 常见陷阱

1. **重启服务前**：先 `nginx -t` 和 `pytest` 都 pass 再敲 systemctl
2. **数据库迁移**：先在本地用 dev DB 跑过，确认 idempotent，再上服务器
3. **流式响应**：客户端断开时**必须**继续读完上游 stream 才能拿到 usage（参见 `app/streaming/sse.py`）
4. **JWT 时区**：`datetime.now(timezone.utc)` 永远显式带 tz；SQLite 默认存 naive，验证时要补 tz
5. **测试 DB 隔离**：每个 test 用 in-memory 引擎，conftest.py fixture 已经处理；**不要**在测试里直接 import `app.db.SessionLocal`
6. **Argon2 验证 vs 比较**：`PasswordHasher().verify(stored_hash, plain)` 不抛异常 = 通过；用 try/except 包起来不要 if/else
7. **OpenAI 流式 usage**：默认不返回，必须显式 `stream_options.include_usage=true`（已在 OpenAIProvider 强制）
8. **Anthropic 流式 usage**：分两个事件——`message_start` 给 input_tokens，`message_delta` 给 output_tokens（streaming pump 已合并）

---

## 9. 当前优先级（2026-05-08）

| 紧急度 | 任务 |
|---|---|
| P0 | 等用户给 Anthropic / OpenAI / Gemini 真实 API Key 做联调验收 |
| P0 | v0.3 开发：支付自动化 + 价格²反比 + cache 粘性 + 邀请返佣 + 阶梯限速 |
| P1 | OAuth (GitHub + Google) 用户提供 client_id+secret 后 1 行命令开通 |
| P2 | 域名 ICP 备案（v1.0 商用前必备） |
| P3 | apex 域名 (`ai100trading.cn` 不带 www) 加 A 记录 + 扩展 SSL 证书 |

---

## 10. 不要假设

如果某个东西没在 `docs/` 或 `CLAUDE.md` 里写明，**问用户**而不是猜。这个项目跨了多 version 演进，命名 / 决策有历史包袱，硬编只会把事搞砸。

---

## 11. 紧急回滚

如果一个 stage 部署后服务挂了：

```bash
ssh ubuntu@43.156.207.26
cd /opt/prism
sudo journalctl -u prism -n 100 --no-pager  # 看错误
sudo systemctl stop prism

# git checkout 上一版本
git log --oneline | head -5
git checkout <last-good-commit>

.venv/bin/pip install -e . --quiet
sudo systemctl start prism
```

数据库回滚（如果 migration 引入问题）：
- 没有自动回滚；从 `/opt/prism/data/prism.db.backup-<date>` 手动恢复（建议每次 migration 前手动 `cp prism.db prism.db.backup-...`）
