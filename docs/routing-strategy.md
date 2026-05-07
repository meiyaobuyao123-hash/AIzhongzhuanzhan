# 路由策略设计文档

> 状态：草稿 · 2026-05-07
> 路由是中转站差异化的核心。本文档描述：当用户请求一个模型时，Prism 网关如何在多条上游渠道里挑一条转发，并在何时切换、何时熔断、何时通知运维。

---

## 0. 问题定义

### 0.1 输入

每条进入网关的请求，路由器拿到的"已知信息"：

```
{
  user_id:    42,
  user_tier:  "developer",      // free / developer / team
  api_key_id: 17,
  request: {
    model: "claude-opus-4.5",
    messages: [...],
    stream: true,
    metadata: {
      // 可选：客户端可以传偏好（仅企业用户生效）
      route_hint: "low-latency"   // 或 "cheapest" / "default"
    },
    // 是否带 Anthropic prompt cache（影响粘性路由）
    cache_control_present: true
  }
}
```

### 0.2 输出

路由器要在毫秒级返回**一条具体的上游 channel**：

```
{
  channel_id:    1,
  provider:      "anthropic",
  base_url:      "https://api.anthropic.com",
  upstream_key:  "sk-ant-real-1...",      // 已解密
  // 元数据，用于扣费 + 日志
  region:        "us-east-1",
  expected_p50:  420,
  expected_cost_per_million_in: 1500000,  // micro-cents
}
```

### 0.3 衡量好路由的 4 个指标

| 指标 | 目标 | 测量 |
|---|---|---|
| **路由延迟** | < 5ms p99 | 网关内部计时 |
| **故障切换成功率** | > 95% | 上游单 channel 故障时整体仍 OK 的比例 |
| **成本效率** | 单 token 成本 ≤ 加权平均上游单价的 1.05× | 月成本 / 月 token |
| **配额利用率** | 单 channel 75% < 利用率 < 95% | 太低浪费、太高易触发限速 |

---

## 1. 路由的 4 层逻辑

```
┌─────────────────────────────────────────────────────────┐
│                    Layer 1: 档位过滤                     │
│  user.tier 决定可用 channel 集合                         │
│    free      → 共享池 default 分组                       │
│    developer → default + dev 分组                        │
│    team      → 私有渠道 + 兜底主池                        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                    Layer 2: 模型过滤                     │
│  request.model 收窄到能跑这个模型的 channel             │
│    claude-opus-4.5 → ch1 (Anthropic 直连),              │
│                     ch3 (Bedrock us-west-2),            │
│                     ch4 (Vertex europe-west4)           │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                    Layer 3: 健康过滤                     │
│  排除 cooldown 中的 channel + 配额耗尽的 channel        │
│    ch1: cooldown until 14:23:45 → 排除                  │
│    ch3: tokens_remaining=120K → 保留                     │
│    ch4: tokens_remaining=0 → 排除                       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                    Layer 4: 加权选择                     │
│  价格²反比加权随机（OpenRouter 同款），                  │
│  + Prompt cache 粘性覆盖（如果命中）                    │
│    最终：ch3                                             │
└─────────────────────────────────────────────────────────┘
                         ↓
                    转发给 ch3
```

---

## 2. Layer 1：用户档位 → 渠道分组

借鉴 New API 的 group 机制，但**对外完全透明**（这是我们的差异化）。

### 2.1 渠道分组

```
default：     基础共享池（Anthropic 直连主账号 + Bedrock 主账号 + ...）
dev：         开发者高优先级（含 prompt cache 优化、专享备份 channel）
team-shared： 企业基础（含 SLA 承诺、含日志 0 保留）
team-{id}：   单租户私有渠道（仅给某个 Team 客户用）
```

### 2.2 档位 → 分组映射

| user_tier | 可用分组 | 说明 |
|---|---|---|
| free | default | 限速最严，与所有人挤同一池 |
| developer | default + dev | dev 分组优先，default 兜底 |
| team | team-{id} + team-shared + default | 私有渠道优先，逐级兜底 |

### 2.3 与同行的区别

| 玩家 | 实现 | 是否透明 |
|---|---|---|
| OpenRouter | 不做档位（统一对待）| - |
| New API（laozhang 等）| 用户买不同套餐解锁不同 group，**用户后台不显示**走的哪个 channel | ❌ 隐式 |
| **Prism** | 同样有档位分组，但**用户控制台明示**走的哪条 channel | ✅ 透明 |

---

## 3. Layer 2：模型 → 可用 channel

### 3.1 数据结构

`models` 表里每个模型记录支持它的 provider；具体 channel 通过 `channels.models` JSON 数组反向匹配。

```
models 表:
  model_id              | provider   | price_input | price_output
  claude-opus-4.5       | anthropic  | 1500000     | 7500000     (micro-cents/M)
  gpt-5                 | openai     | 800000      | 3200000
  gemini-3-pro          | google     | 250000      | 1000000

channels 表:
  id | name              | provider  | models                                    | priority | weight
   1 | Anthropic 主账号  | anthropic | ["claude-opus-4.5","claude-sonnet-4.5"]   | 100      | 60
   2 | Anthropic 备账号  | anthropic | ["claude-opus-4.5","claude-sonnet-4.5"]   | 100      | 40
   3 | Bedrock us-west-2 | bedrock   | ["claude-opus-4.5"]                       | 80       | 30
   4 | OpenAI 主         | openai    | ["gpt-5","gpt-5-mini"]                    | 100      | 100
```

### 3.2 反查算法

```python
def find_candidates(model_id: str, allowed_groups: list[str]) -> list[Channel]:
    return [
        ch for ch in db.channels.where(enabled=True)
        if model_id in ch.models_list
        and ch.group in allowed_groups
    ]
```

---

## 4. Layer 3：健康过滤

### 4.1 channel 状态机

```
   ┌──────────┐  5xx/429   ┌────────────┐
   │  HEALTHY │───────────►│  COOLING   │
   └─────┬────┘            └─────┬──────┘
         │                       │ cooldown 时间到
         │                       ▼
         │                ┌────────────┐
         └────────────────│  HALF-OPEN │ (放 1 个请求试探)
                          └─────┬──────┘
                                │
                          ┌─────┴─────┐
                       成功 │           │ 失败
                          ▼           ▼
                       HEALTHY     COOLING (×2 时长)
```

### 4.2 cooldown 策略

| 触发条件 | cooldown 时长 |
|---|---|
| 单次 5xx | 30s |
| 单次 429 | `Retry-After` header > 0 ? 用它 : 30s |
| 单次 timeout | 30s |
| 1 分钟内 ≥ 3 次 5xx | 5min |
| 5 分钟内 ≥ 5 次 429 | 15min |
| 连续 10 次 ≥ 60s 5xx | 1h（运维介入） |

### 4.3 配额追踪

每次响应解析 Anthropic 的 ratelimit headers：

```
anthropic-ratelimit-tokens-remaining: 287234
anthropic-ratelimit-tokens-reset: 2026-05-07T18:00:00Z
```

写到 Redis 里：

```
prism:channel:1:tokens_remaining = 287234
prism:channel:1:tokens_reset = 1715119200
```

下次路由时，查询此 key，剩余 < 50K 时，跳过此 channel（避免触发 limit）。

### 4.4 与同行对比

| 玩家 | 故障检测 | 自动恢复 | 配额追踪 |
|---|---|---|---|
| OpenRouter | 30 秒窗口 | 自动 | 隐式（重试时实测）|
| New API | 简单 | issue #2899 有 bug | 不做 |
| LiteLLM | cooldown | 自动 | 部分 |
| **Prism** | 状态机 + 渐进式 cooldown | 半开探测 | 显式 Redis 跟踪 |

---

## 5. Layer 4：加权选择

### 5.1 默认算法：价格²反比加权（OpenRouter 同款）

OpenRouter 的核心 IP 之一。**便宜的 channel 概率高，贵的概率低，但贵的也有机会保稳定**。

```python
def weighted_pick(candidates: list[Channel], model: Model) -> Channel:
    # 用户传了 route_hint 优先
    if hint := request.metadata.get('route_hint'):
        if hint == 'cheapest':
            return min(candidates, key=lambda c: cost_for(c, model))
        if hint == 'low-latency':
            return min(candidates, key=lambda c: c.expected_p50)
    
    # 默认：价格²反比加权
    weights = []
    for ch in candidates:
        cost = cost_for(ch, model)  # 该 channel 该模型的真实 input+output 单价
        if cost <= 0:
            weights.append(0)
        else:
            # 价格越低权重越高，平方让差距放大
            w = (1.0 / cost) ** 2
            # 还乘上 channel 的人工 weight（运维可调）
            w *= ch.weight
            weights.append(w)
    
    return random.choices(candidates, weights=weights, k=1)[0]
```

### 5.2 例子

```
ch1: Anthropic 直连     输入 $15/M    weight=60
ch2: Anthropic 备       输入 $15/M    weight=40
ch3: Bedrock us-west-2  输入 $13.5/M  weight=30  (10% 折扣)

价格²反比 weight:
  ch1: (1/15)² × 60 = 0.267
  ch2: (1/15)² × 40 = 0.178
  ch3: (1/13.5)² × 30 = 0.165

归一化概率:
  ch1: 43.8%
  ch2: 29.2%
  ch3: 27.0%
```

ch3 虽然便宜 10%，但因为人工 weight 只有 30，最终命中率不会压倒 ch1（保稳定的 60 weight 占主导）。

### 5.3 不同档位的算法变体

| 档位 | 默认算法 | 备注 |
|---|---|---|
| free | 价格²反比 | 优先用便宜渠道 |
| developer | 价格²反比 + 健康加权 | health > 50 的优先 |
| team-shared | priority 严格降序 | 不冒险，先打主账号 |
| team-{id} | 私有 channel 直接命中（无加权） | 不和别人共享 |

---

## 6. Prompt Cache 粘性路由

### 6.1 为什么需要

Anthropic 的 prompt cache 是**绑定单个上游账号的**：

```
账号 A 缓存了你的 system + 第一条消息（5 分钟 TTL）
你下次请求如果路由到账号 B → cache miss，按全价收费
你下次请求如果路由到账号 A → cache hit，input 部分按 1/10 价（甚至 1/15）
```

如果路由器随机选 channel，**会持续 cache miss，把 prompt cache 这个能力浪费掉**。

### 6.2 粘性算法

```python
def maybe_sticky(request, candidates) -> Channel | None:
    if not request.cache_control_present:
        return None  # 没用 cache 的请求不粘
    
    # 粘性 key = (用户, 模型, 会话指纹)
    fingerprint = hash(request.messages[0:2])  # 第一条 system + 第一条 user
    key = f"{request.user_id}:{request.model}:{fingerprint}"
    
    sticky_id = redis.get(f"prism:sticky:{key}")
    if sticky_id and sticky_id in [c.id for c in candidates]:
        return next(c for c in candidates if c.id == sticky_id)
    
    return None  # 没有粘性记录 → 走默认加权
```

### 6.3 粘性记录的写入

请求成功后：

```python
def record_sticky(request, channel):
    if request.cache_control_present:
        key = sticky_key(request)
        redis.setex(f"prism:sticky:{key}", 5*60, channel.id)  # 5 分钟 TTL
```

### 6.4 触发条件

仅在以下情况启用粘性，否则走默认加权：

1. 请求带 `cache_control` 块
2. 该 channel 的 cache_read_price < 普通 input price 的 50%
3. 粘性 channel 健康（不在 cooldown）

### 6.5 与同行对比

| 玩家 | 粘性策略 |
|---|---|
| OpenRouter | 同上算法（"账户 × 模型 × 对话指纹"）|
| New API | 不做（透传 cache_control 但不粘）|
| **Prism** | 同 OpenRouter |

---

## 7. 容量预警

### 7.1 监控指标（每 channel × 每模型）

每分钟采样一次，写到时序库或 Redis：

| 指标 | 公式 | 阈值 |
|---|---|---|
| TPM 利用率 | 当前分钟 token 数 / channel TPM 限额 | > 85% 黄 / > 95% 红 |
| RPM 利用率 | 当前分钟请求数 / channel RPM 限额 | > 85% 黄 / > 95% 红 |
| 5xx 率（5 min） | 5xx 数 / 总请求 | > 2% 黄 / > 5% 红 |
| 429 率（5 min） | 429 数 / 总请求 | > 5% 黄 / > 15% 红 |
| p95 延迟 | 5 min 滚动 | > 上游基线 1.5× 黄 / 2× 红 |

### 7.2 告警动作

| 等级 | 动作 |
|---|---|
| 黄 | admin 后台 banner 提示，邮件 |
| 红 | 邮件 + 微信机器人 + 自动降低该 channel 的 weight 50% |
| 红 持续 30min | 自动建议运维"该加新账号了"|

### 7.3 容量提示对运营的意义

> 当 Anthropic 主账号 (ch1) 红色 30 分钟连续报警 → 系统自动给运营推一条 "你的 ch1 容量饱和，建议去 console.anthropic.com 注册新账号或申请升 Tier"

这是**半自动**——系统提示运营该做什么，但不替运营登录 Anthropic 创建账号（这是我们之前讨论的边界，详细见 [`docs/upstream-onboarding.md`](upstream-onboarding.md)）。

---

## 8. 实现伪代码（v0.3 完整版）

```python
async def route(request: Request) -> Channel:
    # Layer 1: 档位过滤
    allowed_groups = TIER_TO_GROUPS[request.user.tier]
    
    # Layer 2: 模型过滤
    candidates = await db.channels.where(
        enabled=True,
        group__in=allowed_groups,
        models__contains=request.model,
    )
    if not candidates:
        raise NoChannelAvailable(model=request.model)
    
    # Layer 3: 健康过滤
    healthy = []
    now = utcnow()
    for ch in candidates:
        if ch.cooldown_until and ch.cooldown_until > now:
            continue
        # 配额检查（Redis）
        remaining = await redis.get(f"prism:channel:{ch.id}:tokens_remaining")
        if remaining is not None and int(remaining) < 50_000:
            continue
        healthy.append(ch)
    
    if not healthy:
        # 全 cooldown，紧急放行最快恢复的一条
        healthy = sorted(candidates, key=lambda c: c.cooldown_until or now)[:1]
    
    # Layer 4: 加权选择 + cache 粘性覆盖
    if sticky := await maybe_sticky(request, healthy):
        return sticky
    
    # 用户偏好覆盖
    if hint := request.metadata.get('route_hint'):
        if hint == 'cheapest':
            return min(healthy, key=lambda c: cost_for(c, request.model))
        if hint == 'low-latency':
            return min(healthy, key=lambda c: c.expected_p50)
    
    # 默认：价格²反比加权
    return weighted_pick(healthy, request.model)


async def execute_request(request: Request) -> Response:
    """完整路由 + 重试链"""
    tried = set()
    last_error = None
    
    for attempt in range(MAX_ATTEMPTS):  # 默认 3
        # 排除已经试过的 channel
        candidates = await get_candidates(request)
        candidates = [c for c in candidates if c.id not in tried]
        if not candidates:
            break
        
        ch = await route(request)
        if ch.id in tried:
            break  # 没有新 channel 可试
        tried.add(ch.id)
        
        try:
            resp = await forward(ch, request)
            await record_sticky(request, ch)
            await update_health(ch, success=True)
            return resp
        except Upstream5xx as e:
            await update_health(ch, success=False, error=e)
            last_error = e
            continue
        except Upstream429 as e:
            await set_cooldown(ch, retry_after=e.retry_after or 30)
            last_error = e
            continue
        except UpstreamTimeout as e:
            await update_health(ch, success=False, error=e)
            last_error = e
            continue
    
    raise AllChannelsFailedError(last_error=last_error, tried=tried)
```

---

## 9. 与竞品的横向对比

| 维度 | OpenRouter | New API（laozhang 系）| LiteLLM | Portkey | **Prism** |
|---|---|---|---|---|---|
| 多 channel | ✅ 60+ | ✅ priority+weight | ✅ order=1/2/3 多级 | ✅ weights+order | ✅ priority+weight |
| 加权算法 | 价格²反比 + 故障屏蔽 | 简单加权随机 | 严格按 order 降级 | 按 weights 配置 | **价格²反比 + 用户档位** |
| 故障切换 | ✅ 30s 窗口 | ✅ 部分 | ✅ cooldown | ✅ 5 次指数退避 | ✅ 状态机 + 渐进式 |
| 配额追踪 | 隐式 | 不做 | 部分 | 部分 | **显式 Redis** |
| Cache 粘性 | ✅ 账户×模型×指纹 | ❌ 透传不粘 | ✅ semantic | ✅ semantic | ✅ **同 OpenRouter** |
| 用户档位分流 | ❌ 不做 | ✅ 但不透明 | 取决于配置 | 取决于配置 | ✅ **透明** |
| 容量告警 | ❌ | ❌ | 部分 | ✅ | ✅ |
| 路由透明度 | 高（请求级展示）| 低 | 中 | 中 | **最高（请求级 + 控制台可视化）** |

### 9.1 我们的差异化点

1. **价格²反比 + 用户档位**：OpenRouter 没分档位，国内同行做了档位但不透明，我们做透明的档位分流
2. **Cache 粘性 + Anthropic 优化**：把 OpenRouter 的算法移植到中文场景，并对国内常见 Claude Code 场景做调优
3. **路由可视化**：每条请求展示走的哪条 channel + 为什么选它
4. **半自动容量预警**：系统提示运营，不替运营做（避免风险）

---

## 10. 路线图

| 版本 | 路由能力 | 工作量 |
|---|---|---|
| **v0.1** | 单 channel 直转，无路由 | 0.5 周 |
| **v0.2** | 多 channel + priority+weight + cooldown + 重试 | 1.5 周 |
| **v0.3** | 价格²反比 + 配额追踪 + cache 粘性 + 用户档位 | 2 周 |
| **v1.0** | 容量告警 + 半开探测 + 路由可视化 + Team 私有渠道 | 1.5 周 |

总计：**约 5.5 周**纯路由模块开发，与 PRD 路线图大盘对齐。
