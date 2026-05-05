# AI 中转站竞品调研（2026-05-05）

> 面向准备入局"AI 中转站 SaaS"的中国创业者。覆盖 4 个维度：竞争格局、盈利模式、产品力、路由策略。
> 资料来源时间窗口：截至 2026-05-05 的官网、官方文档、GitHub、知乎/V2EX/LINUX DO/掘金/博客园/V2EX/B 站等公开材料；闭源 SaaS 的内部实现以"用户侧观察"+"开源底座默认行为"的方式合理推断，并在文中明确标注。

---

## 0. 行业速写：这门生意到底在卖什么？

中转站的本质是"把用户付不起或买不到的上游 AI 调用，重新包装成人民币、支付宝、微信、API Key"的二道贩子，赚两头差价：
- **支付差价**：上游用美元信用卡/海外公司主体，下游收人民币、支付宝、USDT；这一段不靠技术也能拿 5-15%。
- **批发-零售差价**：把企业级合同 / 团队订阅 / 逆向 / 云厂商 Bedrock 优惠批发价，按"个人零售单价"卖出去，毛利可以做到 30-300%（真低价区甚至更夸张，因为很多是逆向或共享订阅）。
- **预付沉淀 + 跑路风险**：行业普遍预付费、最低 5 美元起充，资金沉淀本身就是收益，长尾跑路是常态商业模式之一。

腾讯新闻 2026-04-26《月入百万的 AI 中转站，钱到底从哪来？》和 V2EX 多个吐槽帖都把链条拆得很清楚：**反代订阅额度（如 Claude Code Max $200/月对外切片卖）+ 高峰期偷偷降模型 + 同一份流量三头吃（充值费 + 白嫖上游免费额度 + 数据训练/转售）+ 经典生命周期"低价拉人 → 涨价降质 → 跑路"**。

下面我们逐家拆。

---

## 1. 竞争格局总览

| 玩家 | 阵营 | 国别/主体 | 成立 | 规模/口碑 | 目标用户 |
|---|---|---|---|---|---|
| OpenRouter | 全托管 SaaS（品类标杆） | 美国，Alex Atallah（OpenSea 联创）创办 | 2023 | 47 人，年化 inference 收入 1 亿+ 美元，已融 6010 万美元，估值 5 亿美元，A16z 据传以 13 亿估值领投新一轮 | 海外开发者、agent 工具、应用开发商 |
| Helicone | 半托管 / 可观测优先 | 美国 YC W23 | 2023 | 开源 + SaaS，免费 10K req/月，$20/座 | 已有 LLM 应用要做监控/网关 |
| Portkey | 半托管 / 网关优先 | 美国/印度 | 2023 | 路由 1600+ LLM、50+ Guardrails | 中大型企业 prod LLM 应用 |
| LiteLLM (BerriAI) | 开源自部署 + 托管 | 美国 YC | 2023 | OSS 主流，自托管 0 软件费；托管 $49/月起 | 想自己拥有网关的团队 |
| AnyRouter (anyrouter.top) | 半托管，专注 Claude Code | 国内，匿名 | 2025 | 知名度高，被 Linux.do 反复推 | 国内 Claude Code 用户 |
| 老张 AI（laozhang.ai） | 国内全托管 SaaS | 国内 | 2023 起 | 知乎/B 站宣传量大 | 个人/小团队开发者 |
| API2D（api2d.com） | 国内全托管 SaaS（老牌） | 国内（新加坡节点） | 2023 早期 | 老牌，曾是国内门面之一，近年口碑下滑 | 个人开发者、ChatBox 类客户端用户 |
| 云雾 API（yunwu.ai） | 国内全托管 SaaS | 国内 | 2024 | 200+ 模型，主打"0.5 一刀低价" | 价格敏感个人/学生 |
| OhMyGPT（ohmygpt.com） | 国内全托管 SaaS | 国内 | 2023 | 老牌，CDN 多地，相对稳 | 个人 + 小 B 端、Claude Code/Codex 用户 |
| DeepBricks（deepbricks.ai） | 半托管 SaaS（偏小） | 团队信息未公开 | 2024 前后 | 小众，宣传"白菜价 GPT-4o-mini" | 学生 / Indie hacker |
| AiHubMix（aihubmix.com） | 全托管 SaaS（半官方） | 美国主体 AIHubMix, LLC，服务器在 GCP/Azure | 2023 | 自称"Azure/AWS/GCP 授权聚合"，企业向 | 中小企业、品牌方、对稳定性敏感的开发者 |
| ChatAnywhere | 国内全托管 SaaS + 免费 GitHub 项目 | 国内 | 2023 | GitHub `chatanywhere/GPT_API_free` 30k★，国内最大流量入口之一 | 学生、个人薅羊毛 → 付费转化 |
| YesCode（linux.do 系） | 半托管，专攻 Claude Code | 国内匿名 | 2025 | linux.do 社区认知度高 | Claude Code 重度用户 |
| AICodeMirror | 半托管，专攻 Claude Code | 国内 | 2025 | 注册即送 6000 积分，宣传力度大 | Claude Code 个人用户 |
| One API（songquanpeng） | 开源底座 | 个人开发者，国内 | 2023 | OSS 鼻祖，单二进制 + Docker | 自部署的中转站 / 内部分发 |
| New API（QuantumNous & Calcium-Ion） | 开源底座（New API 主流二开） | 国内开发者 | 2023 末 | 目前国内 SaaS 实际事实标准底座 | 中转站站长 |
| VoAPI / DoneHub / Veloera | New API 衍生分支 | 国内开发者群体 | 2024-2025 | 颜值、性能、商业化各有侧重 | 站长二次定制 |
| LobeChat / FastGPT | 前端 / 知识库（生态相邻） | LobeHub（Vincent Chen）/ Labring | 2023 | LobeChat 60k★+，FastGPT 20k★+ | 个人 ChatUI / 企业知识库 |

---

## 2. 海外 / 国际向玩家

### 2.1 OpenRouter（openrouter.ai）—— 行业事实标准

**简介**：由 OpenSea 联合创始人 / 前 CTO Alex Atallah 在 2023 年创办。截至 2026-02 已 47 人，年化 inference 流水从 2024 年底 1000 万美元飙到 1 亿美元+；累计融资 6010 万美元（A16z + Menlo 主导，红杉跟投），传闻 Alphabet Fund 在 2026-04 以 13 亿美元估值领投新一轮。是品类标杆，几乎所有海外 agent 类产品（Cline、Continue、Roo、aider、Open WebUI）默认接入。

**盈利模式**
- **明牌 0% 加价**：模型价格与上游一致，在用户充值环节统一收 **5.5%（最低 0.8 美元）** 平台费。即"充 100 美元，到账 94.5 美元 inference 额度"。
- **BYOK（自带 Key）**：每月前 100 万次免费，超出按调用计费（具体单价另行公布）。
- 没有套餐订阅，没有"团队/企业月费"，纯走 prepaid credits。
- 上游议价：通过把流量从 30+ 主流模型 + 60+ inference provider 拉到一个池里，对单家提供商没强议价但有"流量分配权"，部分小厂会主动给 OpenRouter 上活动价。

**产品力**
- **后台/UI**：业内最干净。模型卡片直接展示每家 provider 的 latency、throughput、context、policy（数据是否被训练）。
- **客户端兼容**：100% OpenAI 兼容。Claude Code、Cursor、Codex、Continue、Cline、ChatBox、LobeChat、aider 全部默认支持；Anthropic 风格 endpoint 也提供。
- **模型覆盖**：300+ 模型，包括所有前沿闭源 + 几乎全部主流开源 + 大量 finetune。
- **能力**：Streaming、function calling、tool use、多模态（image/audio in）、embeddings、structured output、prompt cache passthrough（Anthropic `cache_control` 块原生透传，5 分钟与 1 小时 TTL 在 Anthropic / Bedrock / Vertex 三家全打通）。
- **文档**：业界顶级，几乎每个高级特性都有独立 docs 页（fallbacks、provider-routing、presets、prompt-caching、BYOK 等）。
- **稳定性**：行业最好的之一，靠多 provider 自动 failover；偶有单 provider outage 但平台层面很少全挂。

**路由策略（核心竞争力）**
- **默认负载均衡**：先剔除"最近 30 秒有显著故障"的 provider；在剩余里看价格，**按价格平方反比加权随机** 选一家；其它做 fallback。
- **provider sort**：可显式指定 `sort=price` 或 `sort=latency`，关闭负载均衡变成顺序尝试。
- **model fallbacks**：请求体 `models: ["A","B","C"]` 数组，A 失败自动降级，按最终成功的模型计价。
- **prompt cache 粘性路由**：检测到带缓存的请求后，会把"同一 account × 同一 model × 同一会话指纹（首条 system + 首条 user 的 hash）"粘在同一 provider 上，最大化命中。仅在该 provider 的 cache read 价格低于普通 input 时才启用。
- **BYOK**：60+ provider 支持。
- **内容审核**：仅在上游本身要求时透传（如 Anthropic safety）。OpenRouter 自身不强制内容审核，仅有政策维度的 provider 过滤（"不训练我的数据"等）。

**对国内创业者的启示**：OpenRouter 是不可能在国内 1:1 复刻的，因为它的核心壁垒是**美元支付 + 与 60+ provider 的直采合同 + 可观测仪表盘的极致打磨**。但它的路由算法（价格平方反比 + 故障屏蔽 + sticky cache 路由）几乎是开源底座最该抄的部分。

### 2.2 Helicone

**简介**：YC W23，开源（Apache 2.0）+ SaaS，主线是 LLM observability，2024 年起加入 AI Gateway 模块。

**盈利模式**：免费 10K req/月；$20/座/月起步；企业自部署。
**产品力**：OpenAI 兼容、Anthropic 兼容；session/trace 可视化是行业模板级；100+ 模型、有 semantic cache、failover、rate limit。
**路由策略**：基础多 provider load balance + 自动 failover + cache（语义缓存 + 简单缓存）；不做"按价格加权"那种细操作。

### 2.3 Portkey

**简介**：印度/美国团队，定位"生产级 AI Gateway"。
**盈利模式**：Free 每天 ~330 req；500K req ≈ $36/月，1M ≈ $81，2M ≈ $171；企业版自定义。
**产品力**：Gateway 路由 1600+ LLM、内置 50+ Guardrails、prompt 管理、semantic cache、自动重试（最多 5 次，指数退避）、按权重的多 key/多 provider 负载均衡。
**路由策略**：触发条件可配置的 fallback（按错误码）；按 key/provider 权重的 load balance；有 guardrails 内嵌在路由前后做内容/格式约束。

### 2.4 LiteLLM Proxy（BerriAI）

**简介**：YC 系开源项目，是事实上"自托管 LLM 网关"的标杆，被 LangChain、AutoGen、Cline 等大量集成。
**盈利模式**：OSS 完全免费（自部署）；托管 SaaS：Free → $49/月 prod → 企业自定义。
**产品力**：100+ 模型统一 OpenAI 接口、Redis 共享冷却/限速、按用户/团队/Key 的 budget + TPM/RPM、多模型 fallback、`order=` 优先级、cooldown 自动恢复。
**路由策略**：典型企业网关式路由——`order=1/2/3` 多级优先级；429/500 等错误自动 cooldown 该 deployment；cooldown 期间路由跳到下一级；exponential backoff 重试。注意社区有未关闭 issue（#10052）反映 budget/TPM/RPM 触发后 fallback 不生效，企业版选型时需自测。

### 2.5 AnyRouter（anyrouter.top）

**简介**：国内匿名团队 2025 年起做的"专给国内用户用的 Claude Code 中转"。
**盈利模式**：注册即送 50 美元额度；每日签到送 25 美元额度（社区反复在用这一点拉新）；曾因 GitHub 注册被攻击改成"教育邮箱 / linux.do 账号"才能注册；二级市场流出"225 美元额度账号 8.9 元"。**几乎可以判定后端是反代订阅 / 共享 Max 账号**——50/25 美元这种慷慨额度不可能是官方 API 流量。
**产品力**：只跑 Claude Code 兼容协议；多节点切换；UI 简陋；稳定性"看心情"。
**路由策略**：黑盒。从社区反馈看是多个 Claude 订阅账号轮询 + 节点切换；高峰可能降级到 Sonnet/Haiku。无任何官方文档披露路由细节。

---

## 3. 国内全托管 SaaS

### 3.1 老张 AI（laozhang.ai）

**简介**：国内最早一批中转站之一，2023 年起在知乎/B 站靠"国内最便宜大模型 API"内容做流量，对外 brand 拟人化（"老张"）。
**盈利模式**：充值汇率 **1:7（人民币 7 元 ≈ 美元 1）**，比官方汇率（约 7.2-7.3）略低，等同于人民币入口减 2-3% 折扣；最低 5 美元（35 元）起充；按"分组倍率 × 模型倍率 × (输入 + 输出 × 补全倍率)"扣额度——这是 New API 系经典公式。宣传"价格低至官方 7 折，注册送免费额度"。
**产品力**：覆盖 GPT-5 / GPT-5 mini / o3 / o4-mini / Claude Opus 4.5 / Sonnet 4.5 / Haiku 4.5 / Gemini 3 Pro & Flash / Grok / DeepSeek 等。OpenAI 兼容 + Claude 原生 endpoint，支持 Claude Code、Codex、Cursor、ChatBox、LobeChat。文档使用 Apifox 托管。
**路由策略**：从倍率公式（典型 New API 实现）+ 用户后台展示"分组（default、vip、enterprise）"看，**典型多渠道分组路由**：每个模型挂多条上游 Key，按分组分流，不同分组对应不同质量 / 价格的 channel；高价分组走官转，低价分组可能混合 Bedrock / Vertex / 部分逆向。失败重试是 New API 默认行为（按优先级 + 权重）。无公开 SLA。

### 3.2 API2D（api2d.com）

**简介**：2023 年 4 月起做的早期中转站之一，新加坡节点，是国内"ChatBox + API2D"用户教程套餐里出现率最高的之一。
**盈利模式**：自创"P 点"（1P = 100 Tokens，避免直接对比美元单价），充值人民币最低 21 元；早期主打"国内卡 + 微信支付，无需信用卡"。具体倍率页未对外开放（必须登录），社区反馈倍率不算极致便宜，胜在稳。**核心利润来自支付差价 + 部分套餐月费**。
**产品力**：OpenAI / Claude 兼容；对 ChatBox、ChatGPT-Next-Web、LobeChat 友好；模型清单近年扩到 GPT-5/Claude/Gemini，但产品节奏明显比 laozhang/yunwu 慢半拍；近两年口碑下滑（社区有"老牌但不再首选"的说法）。
**路由策略**：闭源不可知；从产品稳定性和"P 点"机制看，更偏单一渠道托管（不像 laozhang/yunwu 那样明显多分组）。

### 3.3 云雾 API（yunwu.ai）

**简介**：2024 起的新一代中转站，UI 现代，社区营销激进，B 站/V2EX/GitHub 频繁出现。
**盈利模式**：**0.5:1 汇率充值（0.5 元 = 1 美元 token 额度，曾促销到 0.3:1）**——这意味着零售价已经低到官方价的 ~7%-15%。如此低价**几乎不可能是 100% 官转**，社区普遍判断是大量 Bedrock 优惠额度 + 共享订阅 + 部分逆向流量混合。免费层（GitHub 登录）拉新非常猛。207+ 模型。
**产品力**：UI 是 New API 系里颜值前列；模型上新速度快；OpenAI / Claude / Gemini 兼容；Claude Code / Codex 友好。文档简单但够用。
**路由策略**：典型 New API 多分组+权重；从如此激进的价格看，**渠道质量必然分层，且不向用户透明**——这是社区吐槽的主要点。

### 3.4 OhMyGPT（ohmygpt.com）

**简介**：2023 起的老牌中转站之一，定位"企业级 AI 基础设施"，多地 CDN。
**盈利模式**：宣称"约官方 1/5 价格"（社区不同模型实测在官方 0.3-1.2 倍区间，海外用户偶尔出现 1.2 倍）；有月度订阅：**289 元/月含 30 美元/天额度，389 元/月含 40 美元/天额度**——这是典型的"按日额度"包月，类似把 Claude Code Max 切片卖。
**产品力**：100+ 全球模型（Claude、Gemini、GPT、MiniMax、GLM、Qwen，含 Claude Opus 4.5、GPT-5.1max 系列）；Claude Code / Codex 友好；CDN 全球。文档由 Apifox 托管。社区评价稳定性较好。
**路由策略**：闭源；Azure GPT-4 倍率明牌 1.1 暗示走的是 Azure 官方授权而非裸 OpenAI；不同模型不同倍率说明做了按模型路由 + 按渠道分层。

### 3.5 DeepBricks（deepbricks.ai）

**简介**：小众中转，主打"低价 GPT-4o-mini"。
**盈利模式**：白菜价（mini 模型 0.05 美元 / 1M 输入、0.2 美元 / 1M 输出，与官方接近）；最低充值 10 美元；支付宝。
**产品力**：OpenAI 兼容，模型清单较窄；适合"我只想跑 GPT-4o-mini 大批量"的场景。
**路由策略**：闭源；从价格接近官方看不像有逆向，更像走 Azure/官方账号 + 自动重试。社区讨论度低，**作为对照组**：定位窄、流量小、风险也小。

### 3.6 AiHubMix（aihubmix.com）

**简介**：自报主体为美国 AIHubMix, LLC，服务器在 GCP / Azure 美国区域，宣称是 Azure / AWS / GCP 的"授权聚合代理"——这是国内 SaaS 里少见的"半官方"姿态。
**盈利模式**：按量计费、价格大致与官方持平或略低；Claude 模型对外 ≈ 官方 86%；接受支付宝。无公开订阅套餐，主走 prepaid。
**产品力**：200+ 模型，文本/图像/视频/embedding/whisper 全栈；OpenAI / Claude / Gemini 兼容；`api.aihubmix.com/v1` 直接换 base URL 即可；Claude Code、Cursor、Continue、LobeChat、FastGPT 全适配。文档双语。
**路由策略**：从"官方授权"宣传看，主路是 Azure/AWS/GCP 授权 endpoint（实际就是云厂 Bedrock/Vertex 的二次销售）；多渠道做 backup → "production-level unlimited concurrency"（其实是用云厂多实例顶并发）；多模态/embedding/whisper 都在路。

### 3.7 ChatAnywhere

**简介**：2023 起，靠 GitHub 项目 `chatanywhere/GPT_API_free`（30k★，2.2k fork）做最大流量入口，付费转化在自家站。
**盈利模式**：**Freemium 漏斗**——免费版 GPT-5 / 4o 5 次/天、DeepSeek 30 次/天、4o-mini & 3.5-turbo 200 次/天，对每个 IP+Key 限额 200 次/天；付费版"30 元个人用半年 4o-mini"。这是国内中转站里最经典的"内容 + 免费额度"获客打法。
**产品力**：双域名 `api.chatanywhere.tech`（国内）+ `.org`（海外）；OpenAI 兼容；与 ChatBox 类客户端深度绑定文档。
**路由策略**：免费层显然走逆向 + 共享 Key + 严格限速；付费层有更稳的官转池。具体路由不公开。

### 3.8 YesCode

**简介**：2025 年 linux.do 社区项目，专攻 Claude Code 中转。
**盈利模式**：明牌"使用 200 美元 MAX Plan 账号作后端"——也就是订阅切片转售。计费有两条线：订阅制（日更额度 + 月度总额度）、API 单独计费（约 $25 买 $100 额度）。还提供 Kimi / DeepSeek / Gemini 后端。
**产品力**：仅在 Claude Code 这一个客户端协议下打磨；UI 简单；文档社区帖。
**路由策略**：黑盒；本质是 N 个 Max 订阅账号轮询 + 自家限速。

### 3.9 AICodeMirror（aicodemirror.com / .cn）

**简介**：2025 起的 Claude Code 镜像站。
**盈利模式**：注册送 6000 积分（活动期 3000 + 邀请 1000）；按积分扣费，**0:00-8:00 空闲价低，12:00-18:00 高峰浮动**——明显是把上游订阅瓶颈映射到下游分时计价上。10 美元/月套餐对标官方 Pro 20 美元、每日 8000 积分（≈ API 8 美元）。免费池 + 付费池双轨。
**产品力**：仅 Claude Code；纯按量；UI 中规中矩。
**路由策略**：黑盒；从分时定价看，后端也是有限的订阅账号池子。

---

## 4. 开源底座（站长必读）

### 4.1 One API（songquanpeng/one-api）

**简介**：国内开源中转站鼻祖。单二进制 + Docker 一键部署，支持 OpenAI / Azure / Anthropic / Gemini / DeepSeek / 豆包 / 智谱 / 文心 / 星火 / 通义 / 360 / 混元 等。Key 管理 + 二次分发的事实工具。
**核心机制**：Channel（上游 Key）+ Token（用户 Key）+ User + Group 四级模型；每条 Channel 可设置 priority 与 weight（优先级数字大的先用，相同优先级按 weight 加权随机）；模型倍率（model_ratio）+ 补全倍率（completion_ratio）配置文件；失败自动切换下一条 channel；支持 Redis 共享状态。
**适合谁**：想自己起一个站、单人或小团队，快糙猛地把生意先跑起来。

### 4.2 New API（QuantumNous / Calcium-Ion）

**简介**：基于 One API 的二开，目前国内 SaaS 实际事实标准底座（laozhang/yunwu/aihubmix 等大概率在用 New API 系）。原 Calcium-Ion 仓库现已整合到 QuantumNous 主线，Calcium-Ion 维护增强分支 `new-api-horizon`（高性能向）。
**新增 / 强化能力**：
- **多协议互转**：把任意上游统一暴露成 OpenAI 兼容 / Anthropic 兼容 / Gemini 兼容三种格式同时对外（这是国内中转能"既支持 Claude Code 又支持 Cursor 又支持 Codex"的关键）。
- **模型倍率 + 分组倍率**：渠道分组（default、vip、svip 等），不同分组对应不同价格，用户购买不同等级套餐解锁不同分组——这是"低价杀单 + 高价高质"分层的标准做法。
- **签到、邀请、兑换码、卡密、礼品码**：拉新转化全套。
- **失败重试 + 渠道权重**：仍是 priority + weight，社区有 issue（#2899）反映"禁用渠道仍被重试选中"等坑，自部署需注意。
- **缓存**：对 Anthropic prompt cache 透传是支持的（取决于是否开启），自身不做响应级缓存。
**适合谁**：要把 SaaS 跑到收入 10 万以上的站长。

### 4.3 New API 衍生分支：DoneHub / VoAPI / Veloera

- **VoAPI**：颜值与扩展性优先，UI 翻新是主卖点。适合想做"看起来不像中转站"的品牌方。
- **Veloera**：英文 README 强调 intelligent routing / caching / monitoring，海外向 + 自托管。
- **DoneHub**：兼容 OneHub 的凭证体系，针对企业内部分发场景。
- **元聚合层 metapi（cita-777）**：进一步把多个中转站账号聚合成一个入口（自动模型发现 + 智能路由 + 选最便宜的）——这其实就是"OpenRouter for 中国中转站"。

### 4.4 LobeChat / FastGPT（生态相邻）

**LobeChat**（lobehub）：自部署 ChatUI，OpenAI 兼容 + 任何 OpenAI 兼容协议都能接（base_url + key 即可）；接 Claude/Gemini 都走 OpenAI 模式自定义模型。中转站可以把 LobeChat 包成 SaaS 卖（事实上不少站也这么做）。
**FastGPT**（Labring）：知识库 + 工作流编排，对中转站的需求是"我要一个 OpenAI 兼容入口能跑 RAG"——是中转站 to-B 业务的天然消费方。

---

## 5. 横向对比表

### 5.1 定价 / 商业模式

| 玩家 | 充值/订阅模式 | 加价方式 | 折扣/分销 | 主要利润来源 | 高低分层 |
|---|---|---|---|---|---|
| OpenRouter | 充值（5.5%/$0.8 fee） + BYOK（前 100 万免费） | 0% mark-up + 充值费 | BYOK 免费额度 | 充值 fee + 上游补贴 | 不做高低分层（全部官方 endpoint） |
| Helicone | 座位制 $20 起 | 网关功能费 | 自部署免费 | SaaS 月费 | 不分层 |
| Portkey | req 阶梯订阅 | 网关费用 | 免费 → 企业 | SaaS 订阅 | 不分层 |
| LiteLLM | OSS 免费 / Hosted $49 起 | 托管费 | 自部署 0 | 企业版 | 不分层 |
| AnyRouter | 注册送 + 签到送 + 充值 | 不公开 | 邀请 / 签到 | 充值 + 二级市场卖号 | 后端订阅切片 |
| 老张 AI | 1:7 充值 | 0.7-1× 倍率 | 注册送 | 倍率差 + 支付差 | 分组（default/vip） |
| API2D | 1P=100tok 充值 | 不透明倍率 | 月初送 | 支付差 | 不明显 |
| 云雾 API | 0.3-0.5 元/$ 充值 | 极低倍率（0.05-0.3 区间） | 邀请 | 大量低价/逆向流量批发零售差 | 强分层（不透明） |
| OhMyGPT | 充值 + 包月（289/389 元日额度） | 0.3-1.2× | 套餐 | 订阅切片 + 倍率差 | 模型/渠道分层 |
| DeepBricks | 充值（10 美元起） | 接近 1× | 较少 | 支付宝差价 | 弱 |
| AiHubMix | 充值 | ~0.86-1× | 偶有活动 | Bedrock/Vertex 折扣 - 零售价差 | 弱（大都是云厂官方） |
| ChatAnywhere | Freemium → 付费 | 较低 | GitHub 项目导流 | 漏斗转化 | 免费/付费分层 |
| YesCode | 订阅 + API 单独 | $25 买 $100 | 邀请 | Max 订阅切片 | 仅 Claude Code |
| AICodeMirror | 积分制 + 月套餐 | 分时浮动倍率 | 注册送 + 邀请 | Pro/Max 订阅切片 | 时段分层 |

### 5.2 产品力（客户端 / 模型 / 能力）

| 玩家 | OpenAI 兼容 | Anthropic 原生 | Gemini 原生 | Claude Code | Cursor / Codex | 多模态 | 嵌入 | Whisper | 图像生成 | Prompt cache 透传 |
|---|---|---|---|---|---|---|---|---|---|---|
| OpenRouter | ✅ | ✅（含 cache_control） | 部分 | ✅ | ✅ | ✅ | ✅ | 部分 | 部分 | ✅ |
| Helicone | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 部分 | 部分 | 取决于 provider |
| Portkey | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 部分 |
| LiteLLM | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 老张 AI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 部分 | ✅ | ✅（依赖底座） |
| 云雾 API | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 部分 | ✅ | 部分 |
| OhMyGPT | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 部分 |
| AiHubMix | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| API2D | ✅ | ✅ | 部分 | 部分 | 部分 | 部分 | 部分 | 部分 | ✅ | ❓未验证 |
| ChatAnywhere | ✅ | ✅ | ✅ | 部分 | 部分 | 部分 | ✅ | ❓ | 部分 | ❓ |
| AnyRouter | 仅 Anthropic | ✅ | ❌ | ✅ | ❌ | 取决于上游 | ❌ | ❌ | ❌ | 部分 |
| YesCode | 仅 Anthropic | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | 部分 |
| AICodeMirror | 仅 Anthropic | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | 部分 |

### 5.3 路由策略对照

| 玩家 | 多渠道 | 权重/优先级 | 失败重试 | 熔断 | 价格分层 | 按模型路由 | Prompt cache 粘性 | 内容审核 |
|---|---|---|---|---|---|---|---|---|
| OpenRouter | ✅ 60+ | 价格平方反比加权 + 故障屏蔽 | ✅ | ✅（30 秒窗口） | ❌（统一价） | ✅ | ✅（账户×模型×对话指纹） | 仅透传上游政策 |
| Portkey | ✅ | weights + order | ✅（5 次指数退避） | ✅ | 取决于配置 | ✅ | semantic cache | Guardrails 50+ |
| LiteLLM | ✅ | order=1/2/3 多级 | ✅ | ✅（cooldown） | 取决于配置 | ✅ | semantic cache（OSS） | 可配置 |
| Helicone | ✅ | 简单 | ✅ | ✅ | ❌ | ✅ | 语义+简单 cache | 可配置 |
| One API/New API 系（站长底座） | ✅ | priority + weight | ✅ | 部分（issue 在修） | ✅（分组倍率） | ✅ | 透传（依赖渠道） | 可外挂敏感词 |
| 老张/云雾/OhMyGPT/AiHubMix | ✅（推断） | 推断同 New API | ✅ | 推断 | ✅（隐式分组） | ✅ | 部分透传 | 国内站普遍接入第三方审核 |
| AnyRouter/YesCode/AICodeMirror | ✅（订阅池） | 黑盒 | ✅ | ❓ | 时段/套餐 | 单一 | 基本不做 | 不公开 |

---

## 6. 总结观察

**1. 这门生意的两极正在拉开。** 海外是 OpenRouter 一家把"0% 加价 + 充值费 + 极致路由"做成了赢家通吃的标杆；国内则反过来，前 5 家中转站的 SKU 几乎一模一样，差异化卷价格。**国内不是没有 OpenRouter 的位置，是没有人做出 OpenRouter 那种"敢承诺 0 加价"的产品**——因为成本是真的下不来（缺企业合同）。

**2. New API 已经把"做一个站"的门槛降到周末项目。** 现在一个开发者花 2 小时部署 New API + 1 张腾讯云 + 1 个支付宝商户号 + 1 张海外信用卡，就能上线。这意味着：**任何"只是更便宜一点"的差异化都会在 3 个月内被抹平**。

**3. 真正的护城河只有四种：**
- **支付/合规**（拿到对公收款 + 能开发票 + 数据不出境，企业客户愿意签合同）
- **稳定性**（多 provider failover + 自家 SRE + 可观测仪表盘对客户开放）
- **客户端深度集成**（Claude Code / Cursor / Codex 这种工具流量大，谁能做到"换一个 base URL 就什么都好用"，谁就能截流）
- **特定场景包**（如"Claude Code 拼车"、"知识库一站式"）

**4. 路由分层已经是潜规则。** 几乎所有国内非企业向中转站都做了"低价分组（混合渠道，可能含逆向 / 共享订阅）+ 高价分组（官转 / Bedrock / Vertex）"，但很少明牌写出来。**OpenRouter 的"明牌透明"在国内反而是一个未被占据的位置**。

**5. Claude Code 是 2025-2026 中转站最大的单一驱动力。** AnyRouter / YesCode / AICodeMirror / OhMyGPT 月订阅 / 老张的"日额度套餐"——形态各异，本质都是"把 Anthropic Max $200 切片对外卖"。这个生态需要 Anthropic 一停服或一波风控就会大震荡，**重压在 Claude Code 单点上很危险**。

**6. 上游议价权才是真正的天花板。** OpenRouter 已经在跟 Anthropic、OpenAI、Google 单独谈商业合约；国内中转站普遍还在"自己开 API + 反代订阅 + 借朋友的企业 Key"阶段。**谁先在国内拿到 Bedrock / Vertex / Azure 的官方代理资格，谁就能在 to-B 战场建立第一道护城河**——AiHubMix 的官网话术就是奔着这个去的。

---

## 7. 给国内创业者的几条启示

**A. 差异化建议**

1. **明牌定价 + 渠道透明**：模仿 OpenRouter 的"每个模型展示哪些渠道、各自的政策、延迟、context"，国内目前没人做。把"官转 / Bedrock / Vertex / 共享订阅"明牌标注，对企业客户立刻形成信任溢价，可以收 1.05-1.1× 价格；对个人用户保留低价分组。
2. **客户端无感切换**：把 base URL 调整成可以同时挂多个客户端协议（OpenAI / Anthropic / Gemini）的统一入口，且**主动适配 Claude Code、Cursor、Codex、Continue、Roo、aider、Cline、ChatBox、LobeChat、FastGPT**。开个"客户端适配矩阵"页，配截图教程，转化率会高于堆 SKU。
3. **企业版（合规 + 发票 + SLA）**：一开始就做对公合同模板、增值税专票、内容审核 SDK（接腾讯/阿里/讯飞文本审核 + 图像审核）、数据不出境承诺。这是绝大多数 New API 系站长不愿意做的脏活，但企业客户愿意为此付 30%+ 溢价。
4. **可观测面板对客户开放**：用量、成本、按 Key/Project 拆分、p50/p95 延迟、按渠道命中率——把 Helicone/Portkey 的可视化抄过来。中国中转站普遍不做，差异化非常大。
5. **专做一个垂直场景再扩**：例如"Claude Code 中转 + 拼车 + 自动续期 + 失败回切" 一站式产品，把 AnyRouter/YesCode/AICodeMirror 各家的优点合一起；或"FastGPT/Dify 企业知识库托管中转"（OpenAI 兼容 + embedding + Whisper + 图像）。

**B. 主要的坑**

1. **支付通道**：稍微大一点的流水会触发风控，**对公账户 + 营业执照 + 增值税发票** 必须从 day 1 准备；个人卡跑量会被冻结。
2. **逆向/反代订阅依赖**：只要做"低价拉新"，就一定要混逆向或订阅切片，这两条都是定时炸弹（Anthropic 持续做反订阅切片技术封锁，OpenAI 收紧团队订阅审计）。
3. **跑路 / 信任危机**：行业平均生命周期 6-18 个月，预付沉淀越多，用户越警觉。**对小额无所谓，对企业大单必须能开月结合同**。
4. **模型偷换 / 暗中降级**：高峰期把 Sonnet 当 Opus 卖、把 4o 当 5 卖是行业陋习。社区会用 prompt 探针抓你（"你是什么模型 / 输出特定 token 概率"）。
5. **合规风险**：内容审核（生成式 AI 备案 + 文本/图像安全）做不到位，被属地网信办约谈直接关站。
6. **New API 默认 bug**：禁用渠道仍被重试选中、retry 候选重复 channel_id 等已知 issue（#2899）需要打 patch；Redis 共享状态在多机部署下要做幂等。
7. **客户端协议蠕变**：Claude Code、Cursor、Codex 都在快速迭代协议（tool use、prompt cache、extended thinking、artifacts），适配层不持续维护，会被用户用脚投票。

**C. 机会窗口**

1. **企业级 + 合规**：国内目前没有一个"既能给 GPT-5/Claude/Gemini，又有数据不出境承诺、又能开专票、又能签 SaaS 合同"的强心智品牌。AiHubMix 在尝试，但品牌识别度不够。这是最大的窗口。
2. **OpenRouter 中国镜像（明牌透明派）**：直接抄 OpenRouter 的产品形态，但用人民币 / 微信 / 支付宝结算，主动放弃逆向和订阅切片，靠"签更多 Bedrock/Vertex 渠道"做毛利。前期会比对手贵，但企业客户买单。
3. **客户端原生包**：把 Claude Code 的"国内一键安装包 + 默认配好"做成产品（带分时分包、失败回切、对话历史本地缓存）。AICodeMirror 已经在做，但产品力弱。
4. **垂直行业知识库 + 中转**：法律、医疗、电商客服 → 给一份"开箱即用 RAG + 中转 API + 月度报表"产品，对小 B 是真痛点，竞争少。
5. **元聚合（"中转站的中转站"）**：metapi 已经开了头，做"自动比价 + 自动选最便宜健康渠道"的二级聚合层。如果你愿意做下游对站长的 B2B2C，这条路有故事可讲。

---

## 8. 信息来源

| # | 标题 | URL | 抓取时间 |
|---|---|---|---|
| 1 | OpenRouter Pricing | https://openrouter.ai/pricing | 2026-05-05 |
| 2 | OpenRouter FAQ | https://openrouter.ai/docs/faq | 2026-05-05 |
| 3 | OpenRouter Provider Routing | https://openrouter.ai/docs/guides/routing/provider-selection | 2026-05-05 |
| 4 | OpenRouter Prompt Caching | https://openrouter.ai/docs/guides/best-practices/prompt-caching | 2026-05-05 |
| 5 | OpenRouter Model Fallbacks | https://openrouter.ai/docs/guides/routing/model-fallbacks | 2026-05-05 |
| 6 | OpenRouter BYOK | https://openrouter.ai/docs/guides/overview/auth/byok | 2026-05-05 |
| 7 | OpenRouter 1M free BYOK requests/月 | https://openrouter.ai/announcements/1-million-free-byok-requests-per-month | 2026-05-05 |
| 8 | The Block：Alex Atallah 募资 4000 万美元 | https://www.theblock.co/post/360093/opensea-co-founder-alex-atallah-raises-40-million-for-ai-startup-openrouter | 2026-05-05 |
| 9 | Tracxn：OpenRouter 公司画像 | https://tracxn.com/d/companies/openrouter | 2026-05-05 |
| 10 | Crunchbase：OpenRouter | https://www.crunchbase.com/organization/openrouter | 2026-05-05 |
| 11 | Menlo Ventures：投资 OpenRouter | https://menlovc.com/perspective/investing-in-openrouter-the-one-api-for-all-ai/ | 2026-05-05 |
| 12 | Helicone GitHub | https://github.com/Helicone/helicone | 2026-05-05 |
| 13 | Helicone 官网 | https://www.helicone.ai/ | 2026-05-05 |
| 14 | Portkey AI Gateway 文档 | https://portkey.ai/docs/product/ai-gateway | 2026-05-05 |
| 15 | Portkey GitHub | https://github.com/Portkey-AI/gateway | 2026-05-05 |
| 16 | TrueFoundry：Portkey Pricing 解析 | https://www.truefoundry.com/blog/portkey-pricing-guide | 2026-05-05 |
| 17 | LiteLLM Routing & Load Balancing | https://docs.litellm.ai/docs/routing-load-balancing | 2026-05-05 |
| 18 | LiteLLM Fallbacks | https://docs.litellm.ai/docs/proxy/reliability | 2026-05-05 |
| 19 | LiteLLM Budgets & Rate Limits | https://docs.litellm.ai/docs/proxy/users | 2026-05-05 |
| 20 | LiteLLM issue #10052（fallback 不生效） | https://github.com/BerriAI/litellm/issues/10052 | 2026-05-05 |
| 21 | AnyRouter 文档 | https://docs.anyrouter.top/ | 2026-05-05 |
| 22 | 知乎：8.9 元用 AnyRouter 体验 Claude Code | https://zhuanlan.zhihu.com/p/1960285064622487191 | 2026-05-05 |
| 23 | 老张 API 官网 | https://api.laozhang.ai/ | 2026-05-05 |
| 24 | 老张 API 文档 | https://docs.laozhang.ai | 2026-05-05 |
| 25 | cursor-ide.com：laozhang 中转 API 使用指南 | https://www.cursor-ide.com/blog/laozhang-api-transit-guide-2025 | 2026-05-05 |
| 26 | API2D 官网 | https://www.api2d.com/ | 2026-05-05 |
| 27 | API2D 文档 | https://www.api2d.com/doc/ | 2026-05-05 |
| 28 | NewApp.ai：API2D 介绍 | https://a.ftqq.com/2023/04/16/api2d/ | 2026-05-05 |
| 29 | 云雾 API 官网 | https://yunwu.ai/ | 2026-05-05 |
| 30 | 云雾 API 定价 | https://yunwu.ai/pricing | 2026-05-05 |
| 31 | GitHub a37836323/-chatgpt4.0-api-key（云雾推广 README） | https://github.com/a37836323/-chatgpt4.0-api-key | 2026-05-05 |
| 32 | OhMyGPT 官网 | https://www.ohmygpt.com/ | 2026-05-05 |
| 33 | OhMyGPT 文档（Apifox） | https://ohmygpt-docs.apifox.cn/doc-3685383 | 2026-05-05 |
| 34 | DeepBricks 官网 | https://deepbricks.ai/ | 2026-05-05 |
| 35 | houshuai.com：DeepBricks 经济实惠的 API 解决方案 | https://houshuai.com/16.html | 2026-05-05 |
| 36 | AiHubMix 官网 | https://aihubmix.com/ | 2026-05-05 |
| 37 | AiHubMix 文档 | https://docs.aihubmix.com/cn | 2026-05-05 |
| 38 | ChatAnywhere GitHub `GPT_API_free` | https://github.com/chatanywhere/GPT_API_free | 2026-05-05 |
| 39 | ChatAnywhere 中转域名 | https://api.chatanywhere.tech/ | 2026-05-05 |
| 40 | linux.do：YesCode Claude Code 中转上线 | https://linux.do/t/topic/801547 | 2026-05-05 |
| 41 | AICodeMirror 官网 | https://www.aicodemirror.com/ | 2026-05-05 |
| 42 | AICodeMirror 定价页 | https://aicodemirror.cn/pricing/ | 2026-05-05 |
| 43 | 博客园：aicodemirror 镜像站评测 | https://www.cnblogs.com/hongshao/p/19074991 | 2026-05-05 |
| 44 | One API GitHub | https://github.com/songquanpeng/one-api | 2026-05-05 |
| 45 | New API GitHub（QuantumNous） | https://github.com/QuantumNous/new-api | 2026-05-05 |
| 46 | New API Horizon（Calcium-Ion） | https://github.com/Calcium-Ion/new-api-horizon | 2026-05-05 |
| 47 | New API issue #2899（禁用渠道仍被重试） | https://github.com/QuantumNous/new-api/issues/2899 | 2026-05-05 |
| 48 | VoAPI GitHub | https://github.com/VoAPI/VoAPI | 2026-05-05 |
| 49 | Veloera 官网 | https://veloera.org/ | 2026-05-05 |
| 50 | metapi GitHub（中转站元聚合） | https://github.com/cita-777/metapi | 2026-05-05 |
| 51 | LobeHub 文档：使用 OpenAI Key | https://lobehub.com/docs/usage/providers/openai | 2026-05-05 |
| 52 | 腾讯新闻：月入百万的 AI 中转站，钱到底从哪来？ | https://news.qq.com/rain/a/20260426A06AV700 | 2026-05-05 |
| 53 | 知乎：AI API 中转站推荐与评测 | https://zhuanlan.zhihu.com/p/2018044893910552640 | 2026-05-05 |
| 54 | 阿里云开发者：8 个 Claude API 中转站对比 | https://developer.aliyun.com/article/1728443 | 2026-05-05 |
| 55 | yiios.com：3 分钟教你判断中转站实际价格 | https://www.yiios.com/post/bu-yao-bei-di-jie-meng-bi-liao-shuang-yan-3-fen-zhong-jiao-ni-ru-he-pan-duan-zhong-zhuan-zhan-de-shi-ji-jie-ge/ | 2026-05-05 |
| 56 | LINUX DO：萌新求问，官转/直连/中转原理 | https://linux.do/t/topic/213588 | 2026-05-05 |
| 57 | V2EX：用中转站省钱，怎么知道没踩坑 | https://www.v2ex.com/t/1210326 | 2026-05-05 |
| 58 | gitcode/CSDN：2026 大模型 API 价格一览 | https://gitcode.csdn.net/69bf8acc0a2f6a37c5995406.html | 2026-05-05 |
| 59 | gitcode/CSDN：Claude 官方价格汇总 2026 | https://gitcode.csdn.net/69c37d7c0a2f6a37c59a28a5.html | 2026-05-05 |
| 60 | OpenRouter Claude Sonnet 4.6 | https://openrouter.ai/anthropic/claude-sonnet-4.6 | 2026-05-05 |

> 备注：以上 URL 在调研时通过 WebSearch 触达；部分中文站点为镜像 / 引文，原始一手数据请以官网为准。市场变化极快（特别是定价、积分政策、套餐结构），实施前必须再次抓取最新一版。
