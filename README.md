# AIzhongzhuanzhan

AI 中转站 SaaS 项目立项资料库。

**已确定方向**：只做 API 转发（不做账户切片），定位"全模型聚合一站式入口"，避开养号 / 反封号 / 记忆污染等结构性风险。

本仓库用来沉淀业务决策所依赖的调研、设计与备忘文档。

## 文档索引

### 调研
- [docs/competitor-analysis.md](docs/competitor-analysis.md) — AI 中转站竞品调研（2026-05-05），覆盖 18 家玩家，从竞争格局 / 盈利模式 / 产品力 / 路由策略 4 个维度横向对比，给国内创业者落地建议。

### 方案
- [docs/prd.md](docs/prd.md) — Prism 产品需求文档（PRD v0.1）：商业模式（**0% 加价 + 万 5 手续费**）/ 用户分层（Self-serve / Team）/ 功能优先级（P0/P1/P2）/ MVP 范围 / 路线图 / 边界。
- [docs/routing-strategy.md](docs/routing-strategy.md) — 路由策略设计：当前 v0.1 实况（单渠道）/ v0.3+ 4 层决策 / 价格²反比加权 / 健康熔断 / Prompt cache 粘性 / 与 OpenRouter / New API / LiteLLM / Portkey 横向对比。
- [docs/upstream-onboarding.md](docs/upstream-onboarding.md) — 上游接入操作手册：Anthropic 手动 / OpenAI 半自动（Admin API）/ Vertex 半自动（service account）/ Bedrock 半自动（IAM）。
- [docs/token-accounting.md](docs/token-accounting.md) — Token 计费准确性：上游 `usage` 字段为真理 / 流式响应处理 / 月底对账流程 / 误差容差 < 0.5% / "差错双倍返"承诺。
- [docs/payment-methods.md](docs/payment-methods.md) — 充值方式：6 种通道（支付宝 / 微信 / USDT-TRC20 / USDT-Solana / USDT-EVM / 对公）/ 万 5 统一手续费 / 收款地址 / v0.1 手动 SOP / v0.3 自动化路径。
- [docs/v0.1-implementation-plan.md](docs/v0.1-implementation-plan.md) — **v0.1 后端 MVP 实施方案**：技术栈选型 / 目录结构 / URL 设计 / 数据库 DDL（7 张表）/ 模块详细设计 / Admin CLI 命令 / 测试策略 / 部署步骤 / 分阶段开发顺序（A 骨架 → B 适配器 → C 路由+流式+计费 → D 部署联调）/ 留出的 placeholder 一览。
- [docs/v0.2-spec.md](docs/v0.2-spec.md) — **v0.2 产品设计**（已上线）：邮箱注册 + OAuth（GitHub/Google）+ JWT / Web 控制台 5 个 tab / 多 channel 路由 + 熔断状态机 + failover / OAI↔Anthropic 协议互转 / Redis 限速。3 张新表 + 4 个字段增量。
- [docs/v0.3-spec.md](docs/v0.3-spec.md) — **v0.3 产品设计**（开发中）：价格²反比加权（OpenRouter 同款）+ Prompt cache 粘性路由 + 阶梯限速联动 / 邀请返佣（5%）+ 首充 1.05× 加成 / **USDT 链上自动监听**（TRC20/Solana/EVM）+ 自动到账匹配 / 容量预警（RPM/TPM/5xx 阈值 → 邮件 + audit）。
- [docs/oauth-setup.md](docs/oauth-setup.md) — OAuth (GitHub/Google) 一键登录 10 分钟配置指南。

### 设计
- [prompts/claude-design-prompts.md](prompts/claude-design-prompts.md) — Claude design 提示词包 v1，完整多页营销站设计提示词（首页 / 模型 / 定价 / 文档 / 控制台 / 登录注册），含品牌候选（Prism / Nimbus / Mesh / Axiom / 百模）、设计系统 token、视觉风格"3D 酒店风"。
- [prompts/models-page-v2-refined.md](prompts/models-page-v2-refined.md) — `/models` 页迭代 prompt v2，把 v1 的 OpenRouter 克隆式卡片网格重构为"按场景挑模型 + 渠道透明 banner + 紧凑表格"的内容架构，保留视觉系统不变。

### 原型
- [site/index.html](site/index.html) — Prism 首页 v2（落地版），10 段长 landing：Hero + 实时切模型 demo / Trust strip / Features / 接入演示 / 客户端兼容 / 按场景挑模型 / 渠道透明 banner / "我们不做的事" / 定价 + 实时计算器 / FAQ / Final CTA。直接 `open site/index.html` 在浏览器看，无需 build。

## 本地预览

```bash
open site/index.html
# 或者
python3 -m http.server 8000 --directory site
# 然后访问 http://localhost:8000
```

## 注意

调研结果时效性强（市场变化以周为单位），所有结论附有抓取时间戳；做业务决策前请先核对当时最新的官网与定价。
