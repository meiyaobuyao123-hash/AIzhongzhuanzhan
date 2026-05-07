# 上游接入操作手册

> 状态：草稿 · 2026-05-07
> 这是一份给"系统运营人"（你自己）看的操作手册。每接入一家新上游 provider 时按本文档对照操作。

---

## 0. 接入模式总览

| Provider | 接入模式 | 你需要给系统什么 |
|---|---|---|
| **Anthropic** | **完全手动** | 每个账号的 sk-ant-... API Key（一次性贴一次，永久使用） |
| **OpenAI** | **半自动** | 一个 sk-admin-... Admin Key + 一个项目 ID（系统按需 mint 子 key） |
| **Google Gemini API** | 手动 | API Key（来自 Google AI Studio） |
| **Google Vertex AI** | **半自动** | GCP project ID + service account JSON |
| **AWS Bedrock** | **半自动** | IAM access key + secret + region 列表 |
| **Azure OpenAI** | 手动 | endpoint URL + API key + deployment name 列表 |
| **国内厂（DeepSeek, Kimi, Zhipu, Qwen）** | 手动 | 各家 API Key |

下面逐家详细说明。

---

## 1. Anthropic（手动）

### 1.1 你要做的事（每次新加账号）

1. 登录 https://console.anthropic.com
2. Settings → API Keys → Create Key
3. 命名：`Prism prod #1`、`Prism prod #2` 等
4. 复制 sk-ant-api03-xxxxxxxxxx
5. 进 Prism admin → 上游渠道 → 新建：
   - 渠道名：`Anthropic 主账号 #1`
   - Provider: `anthropic`
   - Base URL: `https://api.anthropic.com`
   - API Key: 粘贴
   - 支持模型：勾选要暴露的模型（系统会按 catalog 给你列）
   - Priority: 100 / Weight: 60（默认）
6. 点「测试连通」验证 Key 有效，再保存

### 1.2 为什么不能自动

Anthropic 没有公开的"用一个 master key 创建子 key"的 Admin API（Workspaces 是 Enterprise 才有，且需要单独申请）。所以每个 API 账号的 Key 都得手动到 console 创建一次。

### 1.3 容量到顶时怎么办

系统会发邮件 + 控制台 banner："Anthropic 主账号 #1 利用率连续 30min > 90%，建议加新账号"。你按 1.1 步骤再加一个。

---

## 2. OpenAI（半自动）

### 2.1 你要做的事（一次性配置）

1. 登录 https://platform.openai.com
2. 创建一个组织（或用现有的），记下 org ID（`org-xxxxxxxx`）
3. 创建一个 Project："Prism Production"，记下 project ID（`proj_xxxxxxxx`）
4. Settings → Admin Keys → Generate new admin key
   - 名字：`Prism Admin Master`
   - **Scopes**：勾选 `api.management.write` 和 `api.management.read`（用来 mint / 撤销子 key）
   - 复制 `sk-admin-xxxxxxxx`
5. 进 Prism admin → 上游 provider 配置 → OpenAI：
   - Admin Key: 粘贴 sk-admin-...
   - Org ID: org-xxx
   - Project ID: proj_xxx

### 2.2 之后系统自动做什么

- 系统启动时根据需要的容量数自动 mint N 个子 API Key（sk-...）
- 每个子 Key 对应一条 channel，自动写入 channels 表
- 当某条 channel 长期不健康，系统自动撤销并重 mint
- 当配额逼近，系统自动 mint 新 channel（不用你介入）

### 2.3 OpenAI Admin API 我们用到的接口

```
POST  /v1/organization/projects/{project_id}/api_keys     # 创建子 key
GET   /v1/organization/projects/{project_id}/api_keys     # 列出
DELETE /v1/organization/projects/{project_id}/api_keys/{key_id}  # 撤销
GET   /v1/organization/usage                              # 用量
```

文档：https://platform.openai.com/docs/api-reference/admin

### 2.4 安全注意

- Admin Key 是核弹级凭证（能删除整个 project），系统**加密存储**（KMS / age）
- 系统永远不返回 Admin Key 到前端
- 子 key 也只展示前缀 + 后 4 位

---

## 3. Google Gemini API（手动，无自动化方案）

### 3.1 你要做的事

1. 登录 https://aistudio.google.com
2. Get API Key → 创建 / 复制
3. Prism admin → 新建 channel：
   - Provider: `google-aistudio`
   - Base URL: `https://generativelanguage.googleapis.com`
   - API Key: 粘贴
   - 支持模型：Gemini 系列

### 3.2 限制

Google AI Studio Key 没有 Admin API 能让你自动 mint 子 Key。如果你要规模化，建议走下面的 Vertex AI（功能强、限额高、能自动化）。

---

## 4. Google Vertex AI（半自动，推荐企业向）

### 4.1 你要做的事（一次性配置）

1. 在 Google Cloud Console 创建 GCP project（或用现有的）
2. 启用 Vertex AI API + Generative Language API
3. 创建 service account：IAM & Admin → Service Accounts → Create
   - Name: `prism-vertex-sa`
   - 分配角色：`Vertex AI User`、`Service Account Token Creator`
4. 给该 SA 创建 JSON key（Keys → Add Key → Create new key → JSON），下载
5. Prism admin → 上游 provider 配置 → Google Vertex：
   - Project ID: `your-project-123456`
   - Service Account JSON: 粘贴整个 JSON 文件内容
   - Region 列表（多选）：`us-central1`、`europe-west4`、`asia-southeast1` 等

### 4.2 系统自动做什么

- 启动时用 SA 凭证刷 access token（短 TTL，自动续）
- 按 region 创建多条 channel（一个 region 一条）
- 自动监控每个 region 的 quota
- 配额逼近时**提示你**去 GCP Console 申请提升（quota request 是 Google 的人工审批，无法自动化）

### 4.3 GCP quota 提升流程（半自动）

系统弹出提示："Vertex us-central1 配额连续 7 天 > 85%，建议申请提升"，附带：
- 一个直链：`https://console.cloud.google.com/iam-admin/quotas?project={your-id}`
- 申请文案模板（可复制粘贴到 GCP 申请表）

你 5 分钟提交，Google 审核 1-3 天，新配额自动到账，无需再操作系统。

### 4.4 文档

- Vertex AI for Anthropic: https://docs.anthropic.com/en/api/claude-on-vertex-ai
- Service Account: https://cloud.google.com/iam/docs/service-accounts

---

## 5. AWS Bedrock（半自动）

### 5.1 你要做的事(一次性配置)

1. 在 AWS Console 创建 IAM user：`prism-bedrock`
2. 给 IAM 策略：`AmazonBedrockFullAccess`（或更窄的自定义 policy 仅含 InvokeModel）
3. Generate Access Key → 记下 access key ID + secret access key
4. Prism admin → AWS Bedrock：
   - Access Key ID
   - Secret Access Key
   - Region 列表：`us-west-2`、`us-east-1`、`ap-southeast-1` 等

### 5.2 系统自动做什么

- 用 IAM 凭证签 AWS API 请求（SigV4，每次请求即时签名，无需 token 缓存）
- 按 region 创建多条 channel
- 监控 Bedrock service quota（自动）
- 配额逼近 → 提示你走 AWS Service Quotas Console 申请提升

### 5.3 AWS Activate 折扣

如果你公司符合 AWS Startup / Activate 资格（我们这种 SaaS startup 大概率符合），可以申请 $5K-$100K 的 AWS credits。流程：

1. 申请 AWS Activate（https://aws.amazon.com/activate/）
2. 拿到 credits 后绑到主账号
3. credits 自动抵扣 Bedrock 上的所有 inference 费用
4. 这是国内中转站做毛利的关键杠杆之一（参见 [`docs/competitor-analysis.md`](competitor-analysis.md) §3.6 AiHubMix 那条）

---

## 6. 国内厂（DeepSeek / Moonshot / Zhipu / 阿里 Qwen）

### 6.1 通用步骤（每家都类似）

1. 注册各家平台开发者账号
2. 创建 API Key
3. Prism admin → 新建 channel，填 base URL + API Key

### 6.2 各家 endpoint

| 厂商 | Base URL |
|---|---|
| DeepSeek | https://api.deepseek.com |
| Moonshot (Kimi) | https://api.moonshot.cn/v1 |
| 智谱 GLM | https://open.bigmodel.cn/api/paas/v4 |
| 阿里 Qwen (DashScope) | https://dashscope.aliyuncs.com/api/v1 |
| 字节豆包 | https://ark.cn-beijing.volces.com/api/v3 |
| 百度文心 | https://aip.baidubce.com (走 OAuth) |

### 6.3 注意

国内厂大多 OpenAI 兼容（除百度需要 OAuth），所以 channel 配置和 OpenAI 类似，只是改 base URL + 改 API Key。

---

## 7. Azure OpenAI（手动）

### 7.1 你要做的事

1. 在 Azure Portal 创建 OpenAI 资源（要先申请配额）
2. Deploy 你要用的模型（每个模型一个 deployment）
3. 拿到：endpoint URL（`https://{name}.openai.azure.com`）+ API key
4. Prism admin → 新建 channel：
   - Provider: `azure-openai`
   - Endpoint: 上面的 URL
   - API Version: `2024-10-21`（或最新）
   - API Key
   - Deployment 映射：`{model_id}: {deployment_name}` 字典

### 7.2 注意

Azure 的 model 不是直接传 model_id 而是 deployment_name，所以 Prism 这一层要做映射。

---

## 8. 接入优先级建议

按"性价比 + 容量"建议接入顺序：

| 优先级 | 接入项 | 说明 |
|---|---|---|
| **P0** | Anthropic 直连（2-3 把 Key） | Claude 流量是当前最大需求 |
| **P0** | OpenAI 直连（含 Admin Key） | GPT 流量第二大 |
| **P1** | DeepSeek + Kimi（国内便宜模型） | 国内用户高频 |
| **P1** | Gemini API Studio | 试水 Gemini 流量 |
| **P2** | AWS Bedrock（拿到 Activate credits 时） | 降本利器 |
| **P2** | Vertex AI | 长上下文场景必备 |
| **P3** | Azure OpenAI | 企业客户出海可选 |
| **P3** | 智谱 / Qwen / 豆包 | 国内长尾 |

---

## 9. 安全：上游 Key 在 Prism 里怎么存

```
1. 用户在 admin 后台输入 sk-ant-... 后：
   ↓
2. 网关用 application key 加密（AES-256-GCM 或 age）
   ↓
3. 加密结果落到 channels.upstream_key 列（数据库列也额外加密）
   ↓
4. 应用启动时用 master key 解密到内存
   ↓
5. 内存中的 Key 用于实际请求转发
   ↓
6. 应用日志 / 监控 / 错误信息中永远不出现 Key 原文
```

master key 来源（按生产强度递增）：
- v0.1：环境变量 `PRISM_MASTER_KEY`
- v0.3：HashiCorp Vault / AWS KMS / age-encrypted file
- v1.0：硬件 HSM（如果做到企业级）

---

> 操作手册到此为止。每接入新 provider 类型时，本文档要相应更新。
