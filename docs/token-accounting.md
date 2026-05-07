# Token 计费准确性

> 状态：草稿 · 2026-05-07
> 回答的核心问题：客户调用大模型时，**我们记录的 token 数和上游（Anthropic / OpenAI / Google）的统计能不能对得上**？会不会让客户多付，或者让我们少收？

---

## 0. 一句话答案

**我们不自己数 token，照搬上游响应里的 `usage` 字段**。所以：

- **Token 数**：等于上游告诉我们的数（按定义就是同一个数字）
- **金额**：用上游报告的 token 数 × 我们 catalog 里的单价计算
- **月底对账**：和上游账单的差异预期 < 0.5%（流式断连等边界情况导致），不是 0 但小于一笔 5 美元充值的手续费量级

如果某个月差异超过 1%，是 bug，要立刻排查（最常见三种原因见第 5 节）。

---

## 1. 上游 `usage` 字段是真理

每家上游在响应里都返回 token 用量数字。**这个数字就是它将向我们计费的依据**。我们 100% 按它算。

### 1.1 Anthropic 响应

```json
{
  "id": "msg_xxx",
  "model": "claude-opus-4-5",
  "content": [...],
  "usage": {
    "input_tokens":              1234,
    "output_tokens":             5678,
    "cache_creation_input_tokens": 100,
    "cache_read_input_tokens":     50
  }
}
```

- `input_tokens`：本次未命中 cache 的输入 token（按 input 单价计费）
- `output_tokens`：模型输出 token（按 output 单价计费）
- `cache_creation_input_tokens`：写入 cache 的 token（按 cache write 单价，约 input 的 1.25×）
- `cache_read_input_tokens`：从 cache 读到的 token（按 cache read 单价，约 input 的 0.1×）

文档：https://docs.anthropic.com/en/api/messages

### 1.2 OpenAI 响应

```json
{
  "id": "chatcmpl-xxx",
  "model": "gpt-5",
  "choices": [...],
  "usage": {
    "prompt_tokens":     1234,
    "completion_tokens": 5678,
    "total_tokens":      6912,
    "prompt_tokens_details": {
      "cached_tokens":   100   // 命中 prompt cache 的部分
    },
    "completion_tokens_details": {
      "reasoning_tokens": 800  // o-系列模型的思考链 token
    }
  }
}
```

- `prompt_tokens`：输入 token（含 cached_tokens）
- `completion_tokens`：输出 token（**含 reasoning_tokens**，对 o3/o4 系列）
- `cached_tokens`：缓存命中的 prompt 部分，按 0.5× input 计费
- `reasoning_tokens`：思考链，**也按 output 单价计费**（OpenAI 的口径）

文档：https://platform.openai.com/docs/api-reference/chat/object

### 1.3 Google Gemini 响应

```json
{
  "candidates": [...],
  "usageMetadata": {
    "promptTokenCount":      1234,
    "candidatesTokenCount":  5678,
    "totalTokenCount":       6912,
    "cachedContentTokenCount": 100
  }
}
```

文档：https://ai.google.dev/api/generate-content#UsageMetadata

### 1.4 我们的扣费公式（Anthropic 例子）

```
cost_micro_cents =
    input_tokens              × model.price_input
  + output_tokens             × model.price_output
  + cache_creation_input_tokens × model.price_cache_write
  + cache_read_input_tokens   × model.price_cache_read
```

每家上游的字段名不同但语义相同。Provider Adapter 层做归一化，写到 `usage_logs` 表里都是同一个 schema：

```sql
usage_logs (
  prompt_tokens,        -- 等价于 input_tokens / promptTokenCount
  completion_tokens,    -- 等价于 output_tokens / candidatesTokenCount
  cache_read_tokens,    -- 命中 cache 的部分
  cache_write_tokens,   -- 写入 cache 的部分
  reasoning_tokens,     -- OpenAI o-系列的思考链
  cost_micro_cents      -- 上面公式的结果
)
```

---

## 2. 客户端能不能自己核对？

**能，而且应该**。我们在响应里**透传 `usage` 字段**——客户端可以拿这个数字和上游官方文档对比。

也就是说，客户拿 Claude Code / Cursor / 任何 OpenAI SDK 调用我们 API 时，响应体里的 `usage.input_tokens` 等数字**和直连 Anthropic 拿到的完全一致**——因为本来就是 Anthropic 自己算的，我们只是转发。

**这就是"渠道明牌"在 token 层面的体现**：客户的 SDK 看到的 usage 数字，和他们自己拿 sk-ant- 直连看到的，逐字节相等。

---

## 3. 流式响应：usage 在哪？

流式（`stream: true`）下，token 用量信息在**最后一个 SSE chunk** 里：

### Anthropic 流式

```
event: message_start
data: {"type":"message_start","message":{...,"usage":{"input_tokens":1234,"output_tokens":1}}}

event: content_block_delta
data: {...}

...（许多 content delta）...

event: message_delta
data: {"type":"message_delta","delta":{...},"usage":{"output_tokens":5678}}

event: message_stop
data: {"type":"message_stop"}
```

注意 Anthropic：input_tokens 在 `message_start`，最终 output_tokens 在 `message_delta`。**两个事件都要捕获**。

### OpenAI 流式

OpenAI 默认流式 **不返回 usage**（除非设置 `stream_options: { include_usage: true }`）。我们的 OpenAI Adapter **强制启用** `include_usage`，确保最后一个 chunk 含：

```json
data: {"choices":[],"usage":{"prompt_tokens":1234,"completion_tokens":5678,"total_tokens":6912}}
data: [DONE]
```

### 网关怎么处理

```python
async def forward_stream(req, channel):
    final_usage = None
    async for chunk in upstream_response:
        # 透传给客户端
        await client_response.send(chunk)
        # 累积 usage（每条不同 provider 不同结构）
        if usage := extract_usage(chunk, channel.provider):
            final_usage = merge_usage(final_usage, usage)
    
    if final_usage:
        await record_billing(req, channel, final_usage)
    else:
        # 客户端中途断连或上游没返回 usage
        await record_billing_orphan(req, channel)  # 见第 5.2 节
```

---

## 4. v0.1 阶段的简化做法

由于 v0.1 只有 3 条 channel（Anthropic / OpenAI / Gemini 各一），实现可以非常简单：

```python
def calculate_cost(usage: Usage, model: Model) -> int:
    """全部按 micro-cents 整数运算，避免浮点误差。"""
    cost = 0
    cost += usage.input_tokens             * model.price_input_micro_cents       // 1_000_000
    cost += usage.output_tokens            * model.price_output_micro_cents      // 1_000_000
    cost += usage.cache_read_tokens        * model.price_cache_read_micro_cents  // 1_000_000
    cost += usage.cache_write_tokens       * model.price_cache_write_micro_cents // 1_000_000
    cost += usage.reasoning_tokens         * model.price_output_micro_cents      // 1_000_000  # OpenAI 口径
    return cost
```

**所有金钱运算都用整数 micro-cents**（1 美元 = 100_000_000 micro-cents），杜绝浮点累积误差。

---

## 5. 三种可能让对账对不上的情况

### 5.1 客户端中途断开（最常见）

客户发请求 → 我们流式转发 → 客户网络断开 → 我们没收到上游的最终 chunk → **没有 usage 数据**。

但是上游**已经在生成 token，并且会按 stream 已发送的 token 计费**。

处理办法：
1. 我们维持上游的连接读完最终 chunk，**即使客户端已断**——这是核心策略
2. 万一上游也异常（极罕见），按已转发的 byte 数估算 token 数（用 cl100k_base / o200k_base 等 tokenizer 估算，仅作 fallback）
3. 标记为 `status='partial'`，月底对账时这部分单独看

实际产生的损失估计：< 0.1% 月成本。

### 5.2 我们 catalog 里的单价过期

Anthropic / OpenAI 偶尔调价（升级模型、降价促销）。我们的 `models` 表如果没及时更新，会按老价格计费。

防范：
- 每周一次脚本对比：取上游 pricing 页面 + 我们 catalog，差异自动报警
- 月底对账时如果发现某模型成本系统性偏离上游账单 > 0.5%，立即排查

### 5.3 字段解析 bug（最危险）

Provider 升级响应格式（新字段、字段重命名等）→ 我们没更新解析 → 漏算或算多。

防范：
- Provider Adapter 单元测试，每次上游返回新字段时跑 schema 校验
- 每个 provider 我们订阅其 changelog
- 监控 `usage_logs.cost_micro_cents` 的离群值，自动告警

---

## 6. 月底对账流程

```
[第 1 步] 上游账单到手
  Anthropic Console → Billing → "May 2026: $XYZ.AB"
  OpenAI Platform → Usage → "Total spent this month: $..."
  Google AI Studio → Billing → "Tokens consumed by API key..."

[第 2 步] 我们的网关聚合
  SELECT
    channel_id,
    SUM(cost_micro_cents) / 100_000_000.0 AS our_total_usd
  FROM usage_logs
  WHERE created_at BETWEEN '2026-05-01' AND '2026-06-01'
  GROUP BY channel_id;

[第 3 步] 对照
  ch1 (Anthropic):  我们 $58,420.13   |   上游账单 $58,431.05   |   差 $10.92  (0.019%)  ✅
  ch2 (OpenAI):    我们 $12,345.67   |   上游账单 $12,346.12   |   差 $0.45   (0.004%)  ✅
  ch3 (Gemini):    我们 $1,234.56    |   上游账单 $1,500.00    |   差 $265   (17.7%)   ❌ 排查
```

差异 < 0.5%：正常，归因到流式断开 / cache hit miscalculation 等小误差。

差异 > 1%：bug，找原因（参考第 5 节三种）。

---

## 7. 给客户的承诺

我们对外公开承诺：

1. 客户响应里看到的 `usage.input_tokens` / `output_tokens`，**和直连上游 API 拿到的逐字节相等**
2. 单价表（每个模型 input/output/cache 价）公开在 [/pricing](https://www.ai100trading.cn/suanli/#pricing) 页，与上游官方文档实时同步
3. 月底每个用户可下载**完整请求 CSV**（含每条的 prompt_tokens / completion_tokens / cost），自己用 Excel 校对
4. 如发现我们计费 > 上游官方计费 0.5%，**双倍返还差额**

第 4 条是承诺也是品牌锚点——说"透明"容易，敢写"差错双倍返"难。

---

## 8. 一个常被问的问题

> **"那你们靠什么挣钱？"**

不靠 inference 加价，靠：
- 充值通道费 0.05%（万分之五，覆盖银行成本）
- 企业 SLA / 私有渠道 / 月结合同（Team 套餐月费 5K-50K 元）
- 增值服务（高级面板、批处理、私有模型托管等）

详见 [`docs/prd.md`](prd.md) §1。
