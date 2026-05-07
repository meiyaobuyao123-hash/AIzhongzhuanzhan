# Prism 产品需求文档（PRD v0.1）

> 状态：草稿 · 2026-05-07
> 业务定位已锁定，不在本文档争论。MVP 范围、功能优先级、路线图是本文档的核心内容。

---

## 0. 一句话定义

**Prism 是一个透明定价的 AI 模型聚合 API 网关**：把 200+ 主流模型背后的 60+ 上游渠道汇聚成一个 OpenAI 兼容 API，按上游成本（**0% 加价**）向开发者和企业销售。

不做：账号切片（Pro/Max OAuth token 转 API）、暗中降级、加价倍率、藏渠道。

---

## 1. 商业模式

### 1.1 收入来源

| 来源 | 占比预期（Y2）| 说明 |
|---|---|---|
| 充值手续费 | 50% | 5-7%，行业常规，OpenRouter 5.5% / 最低 $0.8 |
| 企业 SLA / 私有渠道 | 25% | Team 套餐月费 5K-50K 元 |
| 可观测增值 | 15% | 高级面板、按 Project 拆分、长期日志保留 |
| 数据增值 / 工具增值 | 10% | Embedding 索引、批处理、定制 finetune 路由等 |

### 1.2 不做的收入

- ❌ inference 加价（即使 1.05× 也不做）
- ❌ 模型暗中降级
- ❌ 私扣余额
- ❌ 不透明渠道

### 1.3 验证依据

OpenRouter 用此模式做到年化 inference 流水 1 亿美元 + 累计融资 6010 万美元（参见 [`docs/competitor-analysis.md`](competitor-analysis.md) §2.1）。我们在国内复刻这个模式，差异化点是：人民币 / 微信 / 支付宝结算 + 中文客户体验 + 国内合规。

---

## 2. 用户分层

| 档位 | 目标人群 | 客单价 | 核心需求 | 关键差异 |
|---|---|---|---|---|
| **Free** | 试用者、学生 | ¥0 起 | 注册送 $5 试一下 | 共享路由 / 限速 60 RPM / 无 SLA |
| **Developer** | 个人开发者、indie hacker | ¥50-2000/月 | 多模型一个 Key，价格透明 | 高优先级路由 / cache 命中价 / 限速 600 RPM / 邀请返佣 5% |
| **Team** | 小 B / 中型企业 | ¥3000-50000/月 | 合规、稳定、可签合同 | 对公收款 / 增值税专票 / 私有渠道 / SLA 99.95% / 月结 / 专属客户经理 |

### 2.1 用户旅程关键节点

```
匿名 → 注册 → 邮箱验证 → 自动送 $5 → 创建 API Key → 改 base URL 跑通第一条请求
                                                                        │
                                                                        ▼
                                                                 控制台看用量 → 充值
                                                                        │
                                                                 → 升级 Developer
                                                                        │
                                                                 → 联系销售签 Team
```

### 2.2 转化漏斗目标（v1.0 上线 6 个月内）

- 注册 → 跑通首条请求：> 60%
- 跑通 → 月充值 ≥ $5：> 25%
- Developer → Team：> 5%（按账号数）

---

## 3. 功能需求

按 P0 / P1 / P2 优先级分类。P0 = MVP 必须，P1 = v0.3 内必须，P2 = v1.0 后再说。

### 3.1 网关核心（P0）

| 编号 | 功能 | 验收标准 |
|---|---|---|
| GW-1 | OpenAI 兼容 `/v1/chat/completions` | 标准请求/响应 + 流式 SSE 通过 OpenAI Python SDK |
| GW-2 | Anthropic 原生 `/v1/messages` | Claude Code 改 `ANTHROPIC_BASE_URL` 直接能用 |
| GW-3 | 鉴权：Prism Key → user 映射 | 失效 Key 返 401，正确 Key 加载用户上下文 |
| GW-4 | 余额前置检查（pre-flight） | 余额 < 预估成本时拒绝并返 402 |
| GW-5 | 上游响应 usage 解析 + 扣费 | 与上游账单月底误差 < 1% |
| GW-6 | usage_logs 写入 + 异步落库 | 每条请求一行，含 status/latency/cost/channel_id |
| GW-7 | 错误码标准化（4xx/5xx → OpenAI 风格） | 客户端无感 |

### 3.2 路由（P0）

| 编号 | 功能 | 验收标准 |
|---|---|---|
| RT-1 | 单 channel 直转 | MVP 用 |
| RT-2 | 多 channel + priority + weight 加权随机 | v0.2 |
| RT-3 | 故障 cooldown（30s 默认，5xx/429 触发） | v0.2 |
| RT-4 | 失败重试 + 跨 channel 切换 | v0.2 |
| RT-5 | 价格²反比加权（OpenRouter 风格） | v0.3 |
| RT-6 | Prompt cache 粘性路由 | v0.3 |
| RT-7 | 用户档位 → 渠道分组路由 | v0.3 |

详细见 [`docs/routing-strategy.md`](routing-strategy.md)。

### 3.3 用户系统（P0）

| 编号 | 功能 | 优先级 |
|---|---|---|
| US-1 | 邮箱注册 + 密码登录 | P0 |
| US-2 | OAuth（GitHub / Google） | P1 |
| US-3 | API Key CRUD（创建 / 命名 / 限速 / 模型白名单 / 撤销） | P0 |
| US-4 | 余额查询 + 用量面板 | P0（最简版） |
| US-5 | 充值（支付宝 / 微信） | P1 |
| US-6 | 邀请返佣（5%） | P1 |
| US-7 | 对公开票 + 月结合同 | P2 |

### 3.4 Admin 后台（P0）

| 编号 | 功能 | 优先级 |
|---|---|---|
| AD-1 | 上游 channel CRUD（手动添加 sk-ant- 等） | P0 |
| AD-2 | 模型管理（catalog 维护 + 单价） | P0 |
| AD-3 | 用户列表 + 余额/封禁 | P1 |
| AD-4 | 用量统计 / 渠道健康仪表盘 | P1 |
| AD-5 | OpenAI Admin API 自动 mint key | P2 |
| AD-6 | GCP IAM 自动创建 service account | P2 |

### 3.5 可观测（P1）

| 编号 | 功能 | 说明 |
|---|---|---|
| OB-1 | 用户控制台：实时用量 / p50p95 / 月成本 | 借鉴 OpenRouter 控制台 |
| OB-2 | 按 Key / Project 拆分用量 | 企业必须 |
| OB-3 | 渠道命中率 + 健康状态 | 给用户看（差异化）|
| OB-4 | 请求详情：路由到哪个上游、token 分解、错误堆栈 | 信任建设关键 |

### 3.6 增值服务（P2）

| 编号 | 功能 |
|---|---|
| VA-1 | Prompt cache 智能管理（自动添加 cache_control） |
| VA-2 | 私有渠道托管（BYOK 反向：客户上传 Key 我们托管） |
| VA-3 | 批处理 API |
| VA-4 | 长期日志保留（30/90/365 天） |
| VA-5 | 模型推荐 / 自动选最便宜健康渠道（meta-routing） |

---

## 4. 非功能需求

### 4.1 性能

- 网关层增加 p50 延迟 < **20ms**（不含上游推理时间）
- p99 < 80ms
- 单实例支持 **2000 并发**（流式连接）
- 流式响应 first-byte < 100ms（不含上游 TTFT）

### 4.2 可用性

- 平台 SLA：**99.95%**（年累计停机 < 4.4h）
- 单 provider 故障 → 30 秒内自动 failover
- 多机房部署目标 v1.0 之后

### 4.3 安全

- 上游 API Key **加密落库**（KMS / age-encrypted）
- Prism Key 仅存 hash + 前缀
- 余额扣减原子操作（DB 事务）
- 限速 + 异常检测（IP / Key 维度）
- 敏感操作日志（管理员行为审计）

### 4.4 合规

- 备案：站点和"生成式 AI"双备案（Team 阶段必须）
- 数据政策：默认上游全用"不训练"渠道；日志保留 30 天，企业可选 0 日志
- 增值税：Team 套餐起开专票

### 4.5 可扩展性

- DB：MVP SQLite → Postgres（Y1 内迁移）
- 横向扩展：网关无状态，状态在 Redis（限速、cooldown）+ Postgres
- 渠道 / 模型 / 用户全部数据驱动，无硬编码

---

## 5. MVP 范围（v0.1，6 周冲刺）

### 5.1 v0.1 功能清单（最窄）

```
仅做：
  ✅ Anthropic 上游单 channel 直转
  ✅ /v1/messages（Anthropic 原生）+ /v1/chat/completions（OpenAI 兼容）
  ✅ 单租户：管理员手动建用户 + 手动加 channel + 手动加余额
  ✅ Prism Key 鉴权 + 余额扣减 + usage_logs
  ✅ 流式响应 + token usage 解析
  ✅ 一个最小 admin CLI（无 UI）

不做：
  ❌ 注册登录
  ❌ 支付集成
  ❌ Web 控制台
  ❌ 多 provider
  ❌ 路由算法（单 channel）
```

### 5.2 v0.1 验收

- 我（用户）拿 Claude Code 设 `ANTHROPIC_BASE_URL=https://api.prism.ai/anthropic` + Prism Key，能稳定使用
- 月底对账：网关 usage_logs 累计成本 vs Anthropic console 账单 误差 < 0.5%
- 单实例 200 并发不报错

### 5.3 路线图后续

| 版本 | 时间 | 重点 |
|---|---|---|
| v0.1 | 第 1-6 周 | 上面 5.1 列的 MVP，自用验证 |
| v0.2 | 第 7-12 周 | OpenAI / Gemini 上游 + 多 channel 路由 + 故障切换 + 注册登录 + 控制台 alpha |
| v0.3 | 第 13-20 周 | 充值（支付宝/微信）+ 价格²反比加权 + cache 粘性 + 渠道分组 + 邀请返佣 |
| v1.0 | 第 21-26 周 | Team 套餐 / 对公开票 / SLA / 私有渠道 / 商用 GA |

---

## 6. 边界（明确不做）

| 不做 | 原因 |
|---|---|
| 账号切片（OAuth token 转 API） | 记忆污染 + 封号 + 违规风险，长期归零概率 > 70%（见 [`docs/competitor-analysis.md`](competitor-analysis.md) §6） |
| 上游加价倍率 | 与"0% 加价"品牌承诺冲突 |
| 模型暗降级（高峰偷换） | 信任根基，一旦发现等于品牌死亡 |
| 不透明渠道 | 同行潜规则，我们的差异化点正好在这里 |
| 国内逆向上游 | 合规风险 + 上游政策对抗 |
| 自家做基模型 | 不是这家公司的能力圈 |

---

## 7. 竞品参考与差异化

参见 [`docs/competitor-analysis.md`](competitor-analysis.md) 完整调研。本节只摘 PRD 决策依据：

| 维度 | OpenRouter | laozhang/yunwu | AiHubMix | **Prism（我们）** |
|---|---|---|---|---|
| 加价模式 | 0% + 充值 5.5% | 倍率分组 0.7-1× | ~0.86-1× | **0% + 充值 5-7%** |
| 渠道透明 | 业内最透明 | 隐式分组 | 半官方姿态 | **明牌 + 请求级可查** |
| 客户端兼容 | OpenAI + Anthropic + 部分 Gemini | 三协议 | 三协议 | **OpenAI + Anthropic + Gemini，零改造** |
| 合规（中文市场）| 美元支付 | 弱 | 中 | **强（专票 + 备案 + 数据不出境）** |
| 路由算法 | 价格²反比 + cooldown 30s | New API priority+weight | 推断同 New API | **学 OpenRouter，加用户档位分流** |

### 7.1 我们的核心差异化（按重要性）

1. **明牌定价 + 渠道透明**（OpenRouter 在国内的对应位）
2. **国内支付 / 合规 / 专票**（OpenRouter 在国内做不到）
3. **客户端零改造**（Claude Code / Cursor / Codex 一键接入）
4. **路由透明可查**（请求级展示走的渠道、region、policy）
5. **企业 BYOK + 私有渠道托管**（差异化高客单 SKU）

---

## 8. 关键决策记录

| 决策 | 时间 | 内容 | 依据 |
|---|---|---|---|
| API-only，不做账号切片 | 2026-05-06 | 永不接 Pro/Max OAuth | 记忆污染 + 长期风险 |
| 0% 加价 | 2026-05-07 | 收入靠充值费 + 增值 | OpenRouter 验证 |
| 静态首页 v2 上线 | 2026-05-07 | 已部署 https://www.ai100trading.cn/suanli/ | 早曝光、快迭代 |
| 后端语言：未定 | - | 候选：Python FastAPI / Go | 待 v0.1 启动前敲定 |
| 数据库：SQLite → Postgres | - | MVP SQLite，Y1 内迁 Postgres | 简化 v0.1 部署 |
| 部署：腾讯云轻量新加坡 | 2026-05-07 | 已有服务器 | 现有资源 |
