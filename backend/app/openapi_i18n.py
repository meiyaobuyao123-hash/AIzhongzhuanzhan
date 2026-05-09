"""i18n overlay for the OpenAPI spec served at /api/openapi.json.

Strategy:
  1. FastAPI builds the spec from route decorators (English defaults below).
  2. `build_localized_openapi(app, lang)` post-processes the spec and overlays
     translations from TRANSLATIONS for:
       - info.description
       - tag descriptions
       - per-endpoint summary + description
       - schema property title + description
  3. Falls back to English if no translation exists for a key.

Add or improve translations by editing TRANSLATIONS below — no code changes
needed. Quality bar: precise, fluent, concise, detailed enough to act on.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from fastapi import FastAPI

SUPPORTED_LANGS = ("en", "zh", "ja", "ko", "fr")
DEFAULT_LANG = "en"


# ─── Top-level description (rendered as the big block at the top of /api-docs)
API_DESCRIPTION_DEFAULT = """
**Prism** — transparent AI gateway. One API, 5 upstream providers, 0% markup.

## Authentication
All `/v1/*` and `/account/*` endpoints require a Prism Key (issued from the
Console). Pass it as either header — the Anthropic-style `x-api-key` is also
accepted so Claude Code and the official anthropic-sdk work unchanged:

```
Authorization: Bearer sk-prism-...
x-api-key: sk-prism-...
```

## Pricing
We pass through the upstream's price exactly — `cost = price`, no markup on
inference. The only fee is **1.5% on top-ups** (top up $10,000 → $9,850
credited). This covers payment rails, on-chain gas and merchant fees. See
[the pricing page](https://www.ai100trading.cn/suanli/#pricing) for live rates.

## Dual-currency wallets
Each user has both a USD wallet (USDC top-ups go here) and a CNY wallet
(Alipay / WeChat top-ups go here). Models priced in USD (Claude / GPT / o1)
debit USD; models priced in CNY (Doubao / MiniMax / abab) debit CNY. If the
matching wallet is empty we fall back across currencies at a fixed FX rate.

## Top-up channels
- **USDC** on TRC20 / Solana / EVM (BSC / Polygon / Arbitrum / ERC20) —
  monitored on-chain, auto-credited within 30 seconds.
- **Alipay / WeChat Pay** — scan + email confirm, manual review within 1h.
- **Bank wire** — Team plan only, monthly settlement + VAT invoice.

## Compatibility
- `POST /v1/chat/completions` — OpenAI-compatible (works with the OpenAI SDK,
  Cursor, Codex, Continue, …).
- `POST /v1/messages` — Anthropic-native (works with Claude Code and
  anthropic-sdk-python).
- Most models are accessible via either endpoint thanks to the
  OpenAI ↔ Anthropic protocol translator.
"""

# ─── Tags (sidebar groups in /api-docs)
OPENAPI_TAGS_DEFAULT = [
    {"name": "messages", "description": "Anthropic-native `/v1/messages` (Claude Code, anthropic-sdk-python)."},
    {"name": "chat",     "description": "OpenAI-compatible `/v1/chat/completions` (OpenAI SDK, Cursor, Codex)."},
    {"name": "models",   "description": "Model catalog — list every model the client may call."},
    {"name": "auth",     "description": "Email / password registration and JWT sessions."},
    {"name": "oauth",    "description": "Federated login via GitHub or Google."},
    {"name": "account",  "description": "Self-service: profile, API keys, balance, top-ups, USDC intents."},
    {"name": "usage",    "description": "Per-request logs, aggregate analytics, request detail with channel transparency."},
    {"name": "health",   "description": "Liveness probe."},
]

# ─── Translation table.
# Each key is a dotted path under the OpenAPI spec; missing keys fall back to en.
# Format keys:
#   info.description
#   tag.<name>.description
#   path.<verb>.<path>.summary
#   path.<verb>.<path>.description
#   schema.<Model>.<field>.title
#   schema.<Model>.<field>.description
TRANSLATIONS: dict[str, dict[str, str]] = {

    # ─── info ───────────────────────────────────────────────────────────────
    "info.title": {
        "en": "Prism Gateway API",
        "zh": "Prism 网关 API",
        "ja": "Prism Gateway API",
        "ko": "Prism Gateway API",
        "fr": "API de la passerelle Prism",
    },
    "info.description": {
        "en": API_DESCRIPTION_DEFAULT,
        "zh": """
**Prism** — 透明的 AI 模型聚合网关。一套 API，5 家上游，0% 加价。

## 鉴权
所有 `/v1/*` 与 `/account/*` 接口都需要 Prism Key（在控制台创建）。两种 Header
都接受 —— Anthropic 风格的 `x-api-key` 也兼容，所以 Claude Code 和官方
anthropic-sdk 不用改一行代码：

```
Authorization: Bearer sk-prism-...
x-api-key: sk-prism-...
```

## 价格
推理调用按上游单价**原样透传** —— `cost = price`，0% 加价。唯一收费是
**充值时 1.5% 手续费**（充 $10,000 实际到账 $9,850），覆盖支付通道 / 链上 gas /
商户费。当前单价见[定价页](https://www.ai100trading.cn/suanli/#pricing)。

## 双币种钱包
每个账户拥有 USD 钱包（USDC 充值进此）和 CNY 钱包（支付宝 / 微信充值进此）。
按美元计价的模型（Claude / GPT / o1）扣 USD 钱包；按人民币计价的模型
（Doubao / MiniMax / abab）扣 CNY 钱包。同币种钱包余额不足时，按预设固定汇率
跨币种扣费。

## 充值通道
- **USDC**：TRC20 / Solana / EVM（BSC / Polygon / Arbitrum / ERC20）—— 链上监听，
  确认后 30 秒内自动到账。
- **支付宝 / 微信支付**：扫码 + 邮件核对，工作时间 1 小时内入账。
- **对公转账**：仅 Team 套餐，月结 + 增值税专票。

## 协议兼容
- `POST /v1/chat/completions` —— OpenAI 兼容（OpenAI SDK / Cursor / Codex /
  Continue 等直接可用）。
- `POST /v1/messages` —— Anthropic 原生（Claude Code 和 anthropic-sdk-python
  直接可用）。
- 大多数模型可以通过任一接口调用 —— 网关内置 OpenAI ↔ Anthropic 协议互译器。
""",
        "ja": """
**Prism** — 透明な AI ゲートウェイ。1 つの API、5 つの上流プロバイダー、マークアップ 0%。

## 認証
すべての `/v1/*` と `/account/*` エンドポイントは Prism Key（コンソールで発行）が
必要です。Anthropic スタイルの `x-api-key` も受け付けるため、Claude Code と
公式 anthropic-sdk はコード変更なしで動作します：

```
Authorization: Bearer sk-prism-...
x-api-key: sk-prism-...
```

## 料金
推論呼び出しは上流の単価をそのまま透過 —— `cost = price`、推論には一切
マークアップなし。料金は**入金時の 1.5% 手数料**のみ（$10,000 入金で $9,850 着金）。
決済路、オンチェーン gas、加盟店手数料をカバーします。最新単価は
[料金ページ](https://www.ai100trading.cn/suanli/#pricing)を参照。

## 2 通貨ウォレット
各ユーザーは USD ウォレット（USDC 入金先）と CNY ウォレット
（Alipay / WeChat 入金先）を持ちます。USD 建てモデル（Claude / GPT / o1）は
USD から、CNY 建てモデル（Doubao / MiniMax / abab）は CNY から引き落とし。
同通貨ウォレットが不足すると固定為替レートで他方から精算します。

## 入金チャネル
- **USDC**：TRC20 / Solana / EVM（BSC / Polygon / Arbitrum / ERC20）—— オンチェーン
  監視、確認後 30 秒以内に自動着金。
- **Alipay / WeChat Pay**：QR スキャン + メール確認、営業時間内 1 時間以内に着金。
- **銀行送金**：Team プラン限定、月次精算 + 適格請求書。

## プロトコル互換性
- `POST /v1/chat/completions` —— OpenAI 互換（OpenAI SDK、Cursor、Codex、Continue 等）。
- `POST /v1/messages` —— Anthropic ネイティブ（Claude Code、anthropic-sdk-python）。
- ほとんどのモデルはどちらのエンドポイントからも呼び出し可能です —— 内蔵の
  OpenAI ↔ Anthropic プロトコル変換器のおかげです。
""",
        "ko": """
**Prism** — 투명한 AI 게이트웨이. 하나의 API, 5개 업스트림, 0% 마크업.

## 인증
모든 `/v1/*` 및 `/account/*` 엔드포인트는 Prism Key(콘솔에서 발급)가 필요합니다.
Anthropic 스타일 `x-api-key` 도 허용하므로 Claude Code 와 공식 anthropic-sdk 는
코드 변경 없이 그대로 동작합니다:

```
Authorization: Bearer sk-prism-...
x-api-key: sk-prism-...
```

## 가격
추론 호출은 업스트림 단가를 **그대로 통과** — `cost = price`, 추론에 마크업 없음.
유일한 수수료는 **충전 시 1.5%**($10,000 충전 → $9,850 입금) 입니다.
결제망 / 온체인 가스 / 가맹 수수료를 충당합니다. 실시간 단가는
[가격 페이지](https://www.ai100trading.cn/suanli/#pricing)에서 확인.

## 이중 통화 지갑
각 사용자는 USD 지갑(USDC 충전)과 CNY 지갑(Alipay / WeChat 충전)을 가집니다.
USD 단가 모델(Claude / GPT / o1)은 USD 에서, CNY 단가 모델
(Doubao / MiniMax / abab)은 CNY 에서 차감합니다. 해당 지갑 잔액이 부족하면
고정 환율로 다른 지갑에서 정산합니다.

## 충전 채널
- **USDC**: TRC20 / Solana / EVM(BSC / Polygon / Arbitrum / ERC20) — 온체인 모니터링,
  확인 후 30초 내 자동 입금.
- **Alipay / WeChat Pay**: QR 스캔 + 이메일 확인, 영업시간 1시간 내 입금.
- **은행 송금**: Team 플랜 전용, 월별 정산 + 부가가치세 세금계산서.

## 프로토콜 호환성
- `POST /v1/chat/completions` — OpenAI 호환(OpenAI SDK, Cursor, Codex, Continue 등).
- `POST /v1/messages` — Anthropic 네이티브(Claude Code, anthropic-sdk-python).
- 대부분 모델은 어느 엔드포인트에서나 호출 가능합니다 — 내장된 OpenAI ↔ Anthropic
  프로토콜 변환기 덕분입니다.
""",
        "fr": """
**Prism** — passerelle IA transparente. Une API, 5 fournisseurs en amont, 0% de marge.

## Authentification
Tous les endpoints `/v1/*` et `/account/*` requièrent une clé Prism (générée
dans la Console). Passez-la dans l'un des deux en-têtes — l'en-tête
`x-api-key` style Anthropic est aussi accepté, donc Claude Code et le SDK
officiel anthropic-sdk fonctionnent sans modification :

```
Authorization: Bearer sk-prism-...
x-api-key: sk-prism-...
```

## Tarification
Les appels d'inférence passent au prix exact de l'amont — `cost = price`,
aucune marge sur l'inférence. Le seul frais est **1,5% à la recharge**
(rechargez 10 000 $ → 9 850 $ crédités). Cela couvre les rails de paiement,
le gas on-chain et les frais marchands. Voir la
[page tarifs](https://www.ai100trading.cn/suanli/#pricing) pour les prix en direct.

## Portefeuilles bi-devises
Chaque utilisateur dispose d'un portefeuille USD (recharges USDC) et d'un
portefeuille CNY (recharges Alipay / WeChat). Les modèles tarifés en USD
(Claude / GPT / o1) débitent l'USD ; les modèles tarifés en CNY
(Doubao / MiniMax / abab) débitent le CNY. Si le portefeuille de la bonne
devise est vide, on bascule à un taux de change fixe.

## Canaux de recharge
- **USDC** sur TRC20 / Solana / EVM (BSC / Polygon / Arbitrum / ERC20) —
  surveillance on-chain, crédit automatique sous 30 secondes après confirmation.
- **Alipay / WeChat Pay** — scan + confirmation par e-mail, validation manuelle
  sous 1h en heures ouvrées.
- **Virement bancaire** — plan Team uniquement, règlement mensuel + facture TVA.

## Compatibilité protocoles
- `POST /v1/chat/completions` — compatible OpenAI (SDK OpenAI, Cursor, Codex,
  Continue, etc.).
- `POST /v1/messages` — natif Anthropic (Claude Code, anthropic-sdk-python).
- La plupart des modèles sont accessibles via l'un ou l'autre endpoint grâce
  au traducteur de protocoles OpenAI ↔ Anthropic intégré.
""",
    },

    # ─── tags ───────────────────────────────────────────────────────────────
    "tag.messages.description": {
        "en": "Anthropic-native `/v1/messages` (Claude Code, anthropic-sdk-python).",
        "zh": "Anthropic 原生 `/v1/messages` 接口（兼容 Claude Code、anthropic-sdk-python）。",
        "ja": "Anthropic ネイティブ `/v1/messages`（Claude Code、anthropic-sdk-python 互換）。",
        "ko": "Anthropic 네이티브 `/v1/messages` (Claude Code, anthropic-sdk-python 호환).",
        "fr": "Endpoint natif Anthropic `/v1/messages` (Claude Code, anthropic-sdk-python).",
    },
    "tag.chat.description": {
        "en": "OpenAI-compatible `/v1/chat/completions` (OpenAI SDK, Cursor, Codex).",
        "zh": "OpenAI 兼容 `/v1/chat/completions` 接口（兼容 OpenAI SDK、Cursor、Codex 等）。",
        "ja": "OpenAI 互換 `/v1/chat/completions`（OpenAI SDK、Cursor、Codex 互換）。",
        "ko": "OpenAI 호환 `/v1/chat/completions` (OpenAI SDK, Cursor, Codex 호환).",
        "fr": "Endpoint compatible OpenAI `/v1/chat/completions` (SDK OpenAI, Cursor, Codex).",
    },
    "tag.models.description": {
        "en": "Model catalog — list every model the client may call.",
        "zh": "模型目录 —— 列出所有客户端可调用的模型。",
        "ja": "モデルカタログ —— クライアントが呼び出せる全モデルを返します。",
        "ko": "모델 카탈로그 — 클라이언트가 호출 가능한 모든 모델을 나열합니다.",
        "fr": "Catalogue des modèles — liste de tous les modèles appelables.",
    },
    "tag.auth.description": {
        "en": "Email / password registration and JWT sessions.",
        "zh": "邮箱 / 密码注册与 JWT 会话管理。",
        "ja": "メール / パスワード登録と JWT セッション。",
        "ko": "이메일 / 비밀번호 가입 및 JWT 세션 관리.",
        "fr": "Inscription par e-mail/mot de passe et sessions JWT.",
    },
    "tag.oauth.description": {
        "en": "Federated login via GitHub or Google.",
        "zh": "使用 GitHub 或 Google 联合登录。",
        "ja": "GitHub または Google による統合ログイン。",
        "ko": "GitHub 또는 Google 통합 로그인.",
        "fr": "Connexion fédérée via GitHub ou Google.",
    },
    "tag.account.description": {
        "en": "Self-service: profile, API keys, balance, top-ups, USDC intents.",
        "zh": "自助管理：账户资料、API Key、余额、充值、USDC 充值订单。",
        "ja": "セルフサービス：プロフィール、API キー、残高、入金、USDC 入金依頼。",
        "ko": "셀프 서비스: 프로필, API Key, 잔액, 충전, USDC 충전 요청.",
        "fr": "Self-service : profil, clés API, solde, recharges, intentions USDC.",
    },
    "tag.usage.description": {
        "en": "Per-request logs, aggregate analytics, request detail with channel transparency.",
        "zh": "请求级日志、聚合分析、请求详情含渠道明牌。",
        "ja": "リクエスト単位のログ、集計分析、チャネル透明性付きの詳細表示。",
        "ko": "요청별 로그, 집계 분석, 채널 투명 공개가 포함된 요청 상세.",
        "fr": "Journaux par requête, analytique agrégée, détail avec transparence de canal.",
    },
    "tag.health.description": {
        "en": "Liveness probe.",
        "zh": "存活探针。",
        "ja": "稼働確認プローブ。",
        "ko": "상태 확인 프로브.",
        "fr": "Sonde de disponibilité.",
    },

    # ─── endpoint summaries (concise human-readable; auto FastAPI gives "Get Me" etc.)
    "path.post./v1/chat/completions.summary": {
        "en": "Chat completion (OpenAI-compatible)",
        "zh": "对话补全（OpenAI 兼容）",
        "ja": "チャット補完（OpenAI 互換）",
        "ko": "채팅 보완 (OpenAI 호환)",
        "fr": "Complétion chat (compatible OpenAI)",
    },
    "path.post./v1/chat/completions.description": {
        "en": "OpenAI-compatible chat-completion endpoint. Accepts the standard request body (`model`, `messages`, `temperature`, `top_p`, `max_tokens`, `stream`, `tools`, …) and returns either a single response or an SSE stream. Every parameter and every response field is forwarded verbatim from/to the upstream provider — only authentication is rewritten.",
        "zh": "OpenAI 兼容的对话补全接口。接受标准请求体（`model`、`messages`、`temperature`、`top_p`、`max_tokens`、`stream`、`tools` 等），返回单次响应或 SSE 流。所有参数和响应字段都与上游一字不改透传 —— 网关只替换鉴权 Header。",
        "ja": "OpenAI 互換のチャット補完エンドポイント。標準的なリクエストボディ（`model`、`messages`、`temperature`、`top_p`、`max_tokens`、`stream`、`tools` 等）を受け取り、単一レスポンスまたは SSE ストリームを返します。全パラメータと全レスポンスフィールドは上流とそのまま透過します —— ゲートウェイは認証ヘッダーだけ書き換えます。",
        "ko": "OpenAI 호환 채팅 보완 엔드포인트. 표준 요청 본문(`model`, `messages`, `temperature`, `top_p`, `max_tokens`, `stream`, `tools` 등)을 받아 단일 응답 또는 SSE 스트림을 반환합니다. 모든 파라미터와 응답 필드는 업스트림과 그대로 통과 — 게이트웨이는 인증 헤더만 교체합니다.",
        "fr": "Endpoint de complétion chat compatible OpenAI. Accepte le corps standard (`model`, `messages`, `temperature`, `top_p`, `max_tokens`, `stream`, `tools`, etc.) et renvoie une réponse unique ou un flux SSE. Chaque paramètre et chaque champ de réponse est transmis verbatim depuis/vers l'amont — seule l'authentification est réécrite.",
    },
    "path.post./v1/messages.summary": {
        "en": "Anthropic Messages API",
        "zh": "Anthropic Messages 接口",
        "ja": "Anthropic Messages API",
        "ko": "Anthropic Messages API",
        "fr": "API Messages Anthropic",
    },
    "path.post./v1/messages.description": {
        "en": "Anthropic-native Messages API. Use this with Claude Code, the official anthropic-sdk-python, or any client that already speaks Anthropic. Supports streaming via the standard `stream: true` flag. The response includes Anthropic-specific fields like `cache_creation_input_tokens`, `cache_read_input_tokens` and the per-tier `ephemeral_5m/1h_input_tokens` cache breakdown — all forwarded unchanged.",
        "zh": "Anthropic 原生 Messages 接口。Claude Code、官方 anthropic-sdk-python 以及任何已经使用 Anthropic 协议的客户端可以直接调用。通过 `stream: true` 启用 SSE 流式响应。响应包含 Anthropic 特有字段（`cache_creation_input_tokens`、`cache_read_input_tokens`、按时间分层的 `ephemeral_5m/1h_input_tokens`），全部原样透传。",
        "ja": "Anthropic ネイティブ Messages API。Claude Code、公式 anthropic-sdk-python、Anthropic プロトコルを使う任意のクライアントから直接呼び出せます。`stream: true` で SSE ストリーミングを有効化できます。`cache_creation_input_tokens`、`cache_read_input_tokens`、時間階層別の `ephemeral_5m/1h_input_tokens` 等 Anthropic 固有フィールドはすべて変更なしで透過されます。",
        "ko": "Anthropic 네이티브 Messages API. Claude Code, 공식 anthropic-sdk-python, Anthropic 프로토콜을 쓰는 모든 클라이언트에서 바로 호출 가능합니다. `stream: true` 로 SSE 스트리밍 활성화. `cache_creation_input_tokens`, `cache_read_input_tokens`, 시간대별 `ephemeral_5m/1h_input_tokens` 등 Anthropic 고유 필드는 모두 변경 없이 통과됩니다.",
        "fr": "API Messages native Anthropic. À utiliser avec Claude Code, le SDK officiel anthropic-sdk-python ou tout client Anthropic. Le streaming SSE s'active via `stream: true`. La réponse inclut les champs spécifiques à Anthropic — `cache_creation_input_tokens`, `cache_read_input_tokens`, le détail `ephemeral_5m/1h_input_tokens` — tous transmis sans modification.",
    },
    "path.get./v1/models.summary": {
        "en": "List available models",
        "zh": "列出可用模型",
        "ja": "利用可能なモデル一覧",
        "ko": "사용 가능 모델 목록",
        "fr": "Lister les modèles disponibles",
    },
    "path.get./v1/models.description": {
        "en": "Returns every model the caller may invoke, in OpenAI's `models.list` format. The `id` field is what you pass as `model` in `/v1/chat/completions` or `/v1/messages`.",
        "zh": "返回当前账号可调用的所有模型，格式与 OpenAI `models.list` 一致。`id` 字段就是 `/v1/chat/completions` 或 `/v1/messages` 请求里 `model` 参数应填的值。",
        "ja": "現在の呼び出し元が利用可能な全モデルを返します。フォーマットは OpenAI の `models.list` と同じ。`id` フィールドが `/v1/chat/completions` や `/v1/messages` の `model` パラメータに渡す値です。",
        "ko": "현재 호출자가 사용 가능한 모든 모델을 OpenAI `models.list` 형식으로 반환합니다. `id` 필드 값을 `/v1/chat/completions` 또는 `/v1/messages` 의 `model` 파라미터에 그대로 전달합니다.",
        "fr": "Renvoie tous les modèles que l'appelant peut invoquer, au format `models.list` d'OpenAI. Le champ `id` est ce que vous passez comme `model` dans `/v1/chat/completions` ou `/v1/messages`.",
    },

    "path.get./account/api-keys.summary": {
        "en": "List API keys",
        "zh": "列出 API Key",
        "ja": "API キー一覧",
        "ko": "API Key 목록",
        "fr": "Lister les clés API",
    },
    "path.post./account/api-keys.summary": {
        "en": "Create an API key",
        "zh": "创建 API Key",
        "ja": "API キー作成",
        "ko": "API Key 생성",
        "fr": "Créer une clé API",
    },
    "path.post./account/api-keys.description": {
        "en": "Creates a new Prism Key. **The full key is returned only once** — store it somewhere safe; afterwards only the prefix and last 4 characters are visible.",
        "zh": "创建一条新的 Prism Key。**完整 Key 只在创建时返回一次**，请立即妥善保存；之后接口只返回前缀和后 4 位。",
        "ja": "新しい Prism Key を作成します。**完全な Key は作成時に一度だけ返されます** —— 安全な場所に保存してください。その後はプレフィックスと末尾 4 桁のみ表示されます。",
        "ko": "새 Prism Key를 생성합니다. **전체 Key는 생성 시 한 번만 반환됩니다** — 안전한 곳에 저장하세요. 이후에는 접두사와 끝 4자리만 표시됩니다.",
        "fr": "Crée une nouvelle clé Prism. **La clé complète n'est renvoyée qu'une seule fois** — conservez-la en lieu sûr ; ensuite seuls le préfixe et les 4 derniers caractères sont visibles.",
    },
    "path.get./account/api-keys/{id}.summary": {
        "en": "Get an API key (metadata)",
        "zh": "查询 API Key 元数据",
        "ja": "API キー情報取得",
        "ko": "API Key 정보 조회",
        "fr": "Détail d'une clé API",
    },
    "path.patch./account/api-keys/{id}.summary": {
        "en": "Update an API key",
        "zh": "更新 API Key",
        "ja": "API キー更新",
        "ko": "API Key 수정",
        "fr": "Mettre à jour une clé API",
    },
    "path.delete./account/api-keys/{id}.summary": {
        "en": "Revoke an API key",
        "zh": "吊销 API Key",
        "ja": "API キー失効",
        "ko": "API Key 폐기",
        "fr": "Révoquer une clé API",
    },
    "path.delete./account/api-keys/{id}.description": {
        "en": "Marks the key as revoked. Clients using it will fail authentication immediately. Irreversible.",
        "zh": "将该 Key 标记为已吊销。任何还在使用此 Key 的客户端立即鉴权失败。**不可恢复**。",
        "ja": "対象 Key を失効状態にします。使用中のクライアントは即時認証失敗。**取り消し不可**。",
        "ko": "해당 Key를 폐기 상태로 표시합니다. 사용 중인 클라이언트는 즉시 인증 실패. **되돌릴 수 없습니다**.",
        "fr": "Marque la clé comme révoquée. Les clients qui l'utilisent échouent immédiatement à l'authentification. Action irréversible.",
    },
    "path.get./account/balance.summary": {
        "en": "Read both wallets",
        "zh": "读取双币种钱包余额",
        "ja": "両ウォレット残高取得",
        "ko": "이중 지갑 잔액 조회",
        "fr": "Lire les deux portefeuilles",
    },
    "path.get./account/balance.description": {
        "en": "Returns USD and CNY wallet balances plus lifetime top-up totals (in micro-units for exact integer math). USDC top-ups go to USD; Alipay/WeChat go to CNY.",
        "zh": "返回 USD 和 CNY 两个钱包的当前余额以及累计充值额（单位为微分，便于整数运算）。USDC 充值进 USD 钱包；支付宝 / 微信充值进 CNY 钱包。",
        "ja": "USD・CNY 両ウォレットの残高と累計入金額を返します（整数演算のため µ 単位）。USDC は USD へ、Alipay / WeChat は CNY へ。",
        "ko": "USD 및 CNY 지갑의 현재 잔액과 누적 충전액을 반환합니다(정확한 정수 연산을 위한 µ 단위). USDC는 USD 지갑, Alipay/WeChat은 CNY 지갑으로 입금됩니다.",
        "fr": "Renvoie les soldes des portefeuilles USD et CNY ainsi que les totaux cumulés de recharge (en micro-unités pour calcul entier exact). USDC va vers USD ; Alipay/WeChat vont vers CNY.",
    },
    "path.get./account/me.summary": {
        "en": "Read current user",
        "zh": "读取当前账号资料",
        "ja": "ログイン中ユーザー情報",
        "ko": "현재 사용자 정보",
        "fr": "Lire l'utilisateur courant",
    },
    "path.patch./account/me.summary": {
        "en": "Update current user",
        "zh": "更新当前账号资料",
        "ja": "ログイン中ユーザー更新",
        "ko": "현재 사용자 수정",
        "fr": "Modifier l'utilisateur courant",
    },
    "path.post./account/topup-intent.summary": {
        "en": "Create a USDC top-up intent",
        "zh": "创建 USDC 充值订单",
        "ja": "USDC 入金依頼を作成",
        "ko": "USDC 충전 요청 생성",
        "fr": "Créer une intention de recharge USDC",
    },
    "path.post./account/topup-intent.description": {
        "en": "Creates a pending USDC top-up. Returns the receiving address and the **exact** amount to send. The amount is amended with a 4-digit µ¢ suffix so concurrent pending intents can be distinguished — sending an unmatched amount will not credit. The chain monitor auto-credits within 30 seconds of on-chain confirmation. Note: the channel field still uses `usdt-*` keys for database compatibility, but we accept USDC tokens.",
        "zh": "创建一条待支付的 USDC 充值订单。返回收款地址和**精确金额**。金额带 4 位 µ¢ 后缀以区分并发的不同充值订单 —— 金额不匹配不会到账。链上确认后 30 秒内由网关自动入账。注：`channel` 字段仍使用 `usdt-*` 命名是为了数据库兼容，实际收的是 USDC token。",
        "ja": "待機中の USDC 入金依頼を作成します。受取アドレスと**正確な金額**を返します。金額には末尾 4 桁の µ¢ サフィックスが付与され、同時並行する複数の依頼を区別します —— 金額が一致しない送金は着金しません。オンチェーン確認後 30 秒以内に自動着金。注：`channel` フィールドはデータベース互換性のため `usdt-*` 名のままですが、実際に受け付けるのは USDC トークンです。",
        "ko": "대기 중인 USDC 충전 요청을 생성합니다. 수신 주소와 **정확한 금액**을 반환합니다. 금액에는 4자리 µ¢ 접미사가 붙어 동시 진행 요청을 구분합니다 — 금액이 일치하지 않으면 입금되지 않습니다. 온체인 확인 후 30초 이내 자동 입금. 참고: `channel` 필드는 데이터베이스 호환을 위해 여전히 `usdt-*` 이름을 사용하지만 실제로는 USDC 토큰을 받습니다.",
        "fr": "Crée une recharge USDC en attente. Renvoie l'adresse de réception et le **montant exact** à envoyer. Un suffixe µ¢ à 4 chiffres distingue les recharges concurrentes — un montant non concordant ne sera pas crédité. Le moniteur on-chain crédite automatiquement sous 30s après confirmation. Note : le champ `channel` utilise toujours des clés `usdt-*` pour compatibilité base de données, mais nous acceptons bien des tokens USDC.",
    },
    "path.get./account/topups.summary": {
        "en": "List top-up history",
        "zh": "查询充值记录",
        "ja": "入金履歴一覧",
        "ko": "충전 내역 목록",
        "fr": "Historique des recharges",
    },

    "path.post./auth/register.summary": {
        "en": "Register a new account",
        "zh": "注册新账号",
        "ja": "新規アカウント登録",
        "ko": "새 계정 가입",
        "fr": "Créer un compte",
    },
    "path.post./auth/login.summary": {
        "en": "Log in with email + password",
        "zh": "邮箱 + 密码登录",
        "ja": "メール+パスワードでログイン",
        "ko": "이메일+비밀번호로 로그인",
        "fr": "Se connecter (e-mail + mot de passe)",
    },
    "path.post./auth/logout.summary": {
        "en": "Log out (revoke current session)",
        "zh": "退出登录（吊销当前会话）",
        "ja": "ログアウト（現セッションを失効）",
        "ko": "로그아웃 (현재 세션 폐기)",
        "fr": "Se déconnecter (révoquer la session)",
    },
    "path.post./auth/logout.description": {
        "en": "Revokes the current session token. Idempotent — calling it on an already-logged-out client returns success.",
        "zh": "吊销当前会话的 JWT。**幂等**操作 —— 已经退出登录的客户端再次调用也返回成功。",
        "ja": "現在のセッショントークンを失効させます。**冪等**な操作 —— ログアウト済みクライアントが再度呼び出しても成功します。",
        "ko": "현재 세션 토큰을 폐기합니다. **멱등** 동작 — 이미 로그아웃된 클라이언트가 다시 호출해도 성공을 반환합니다.",
        "fr": "Révoque le jeton de session courant. **Idempotent** — un appel sur un client déjà déconnecté renvoie un succès.",
    },
    "path.post./auth/change-password.summary": {
        "en": "Change current password",
        "zh": "修改当前密码",
        "ja": "パスワード変更",
        "ko": "비밀번호 변경",
        "fr": "Changer le mot de passe",
    },
    "path.post./auth/forgot-password.summary": {
        "en": "Request a password-reset email",
        "zh": "请求重置密码邮件",
        "ja": "パスワード再設定メールを送信",
        "ko": "비밀번호 재설정 이메일 요청",
        "fr": "Demander un e-mail de réinitialisation",
    },
    "path.post./auth/forgot-password.description": {
        "en": "Sends a password-reset email if the address exists. **Always returns success** so the response cannot be used to probe whether an email is registered.",
        "zh": "若邮箱已注册则发送重置邮件。**无论邮箱是否存在都返回成功**，避免响应被用于探测账号是否已注册。",
        "ja": "登録済みであれば再設定メールを送信します。**メール存在の有無に関わらず常に成功を返します** —— レスポンスをアカウント存在の調査に使われないためです。",
        "ko": "등록되어 있으면 재설정 이메일을 발송합니다. **이메일 존재 여부와 무관하게 항상 성공을 반환합니다** — 응답으로 계정 존재를 탐지하는 것을 방지하기 위함입니다.",
        "fr": "Envoie un e-mail de réinitialisation si l'adresse existe. **Renvoie toujours un succès** afin que la réponse ne révèle pas si un e-mail est enregistré.",
    },
    "path.post./auth/reset-password.summary": {
        "en": "Reset password with token",
        "zh": "凭重置 token 设置新密码",
        "ja": "トークンでパスワード再設定",
        "ko": "토큰으로 비밀번호 재설정",
        "fr": "Réinitialiser avec un token",
    },
    "path.post./auth/verify-email.summary": {
        "en": "Verify email by token",
        "zh": "凭 token 验证邮箱",
        "ja": "トークンでメール認証",
        "ko": "토큰으로 이메일 인증",
        "fr": "Vérifier l'e-mail par token",
    },
    "path.get./auth/oauth/providers.summary": {
        "en": "List configured OAuth providers",
        "zh": "列出已启用的 OAuth 登录方式",
        "ja": "設定済み OAuth プロバイダー一覧",
        "ko": "구성된 OAuth 프로바이더 목록",
        "fr": "Lister les fournisseurs OAuth configurés",
    },
    "path.get./auth/oauth/providers.description": {
        "en": "The login page calls this on load to know which buttons to show (GitHub / Google / …). Returns each provider's name and a `configured` flag.",
        "zh": "登录页加载时调用，用于决定显示哪些第三方登录按钮（GitHub / Google 等）。每个 provider 返回名称和 `configured` 标志。",
        "ja": "ログインページがロード時に呼び出し、表示すべきボタン（GitHub / Google 等）を判断するために使います。各プロバイダーの名前と `configured` フラグを返します。",
        "ko": "로그인 페이지 로드 시 호출되어 표시할 버튼(GitHub / Google 등)을 결정합니다. 각 프로바이더의 이름과 `configured` 플래그를 반환합니다.",
        "fr": "Appelé au chargement de la page de connexion pour savoir quels boutons afficher (GitHub / Google / …). Renvoie le nom et le flag `configured` de chaque fournisseur.",
    },
    "path.get./auth/oauth/{provider_name}/authorize.summary": {
        "en": "Start OAuth flow",
        "zh": "发起 OAuth 流程",
        "ja": "OAuth フロー開始",
        "ko": "OAuth 플로우 시작",
        "fr": "Lancer le flux OAuth",
    },
    "path.get./auth/oauth/{provider_name}/callback.summary": {
        "en": "OAuth callback",
        "zh": "OAuth 回调",
        "ja": "OAuth コールバック",
        "ko": "OAuth 콜백",
        "fr": "Callback OAuth",
    },

    "path.get./usage/stats.summary": {
        "en": "Aggregate usage statistics",
        "zh": "聚合用量统计",
        "ja": "集計使用量統計",
        "ko": "집계 사용량 통계",
        "fr": "Statistiques d'utilisation agrégées",
    },
    "path.get./usage/requests.summary": {
        "en": "List request log",
        "zh": "查询请求明细",
        "ja": "リクエストログ一覧",
        "ko": "요청 로그 목록",
        "fr": "Lister le journal de requêtes",
    },
    "path.get./usage/requests/{request_id}.summary": {
        "en": "Single request detail (channel transparency)",
        "zh": "单条请求详情（含渠道明牌）",
        "ja": "単一リクエスト詳細（チャネル透明性付き）",
        "ko": "단일 요청 상세(채널 투명 공개)",
        "fr": "Détail d'une requête (transparence du canal)",
    },
    "path.get./usage/requests/{request_id}.description": {
        "en": "**The channel-transparency panel.** Returns the exact upstream channel that served this request — provider, region, no-training/log-retention policy, retry history if a failover happened. This is the core differentiator from competitors who hide which upstream actually served you.",
        "zh": "**渠道明牌面板。** 返回服务此请求的真实上游渠道 —— provider、region、不训练/日志保留策略、若发生过 failover 则附带重试历史。这是 Prism 与「藏渠道」竞品的核心区别。",
        "ja": "**チャネル透明性パネル。** このリクエストを処理した実際の上流チャネル —— provider、region、学習しない/ログ保持ポリシー、フェイルオーバーが発生した場合は再試行履歴 —— を返します。これがチャネルを隠す競合との中核的な差別化点です。",
        "ko": "**채널 투명 공개 패널.** 이 요청을 처리한 실제 업스트림 채널 — provider, region, 학습 안 함 / 로그 보존 정책, 페일오버가 있었다면 재시도 이력 — 을 반환합니다. 이는 채널을 숨기는 경쟁사 대비 핵심 차별점입니다.",
        "fr": "**Panneau de transparence du canal.** Renvoie le canal en amont exact qui a servi cette requête — fournisseur, région, politique no-training/rétention des logs, et historique de retry en cas de bascule. C'est notre différenciateur clé face aux concurrents qui cachent leur routage.",
    },
    "path.get./usage/models.summary": {
        "en": "Distinct models the caller has used",
        "zh": "当前账号调用过的去重模型列表",
        "ja": "呼び出し元が使った重複削除済みモデル一覧",
        "ko": "호출자가 사용한 중복 제거 모델 목록",
        "fr": "Modèles distincts utilisés par l'appelant",
    },
    "path.get./usage/models.description": {
        "en": "Returns the 50 most-recently-used model_ids for the caller, each with call count and last-used timestamp. Used by the console's filter dropdown so users only see relevant models.",
        "zh": "返回调用者最近使用过的 50 个 model_id（去重），每条带调用次数和最后一次使用时间。控制台用量筛选下拉框使用此接口，只显示用户实际用过的模型。",
        "ja": "呼び出し元が最近使用した model_id を最大 50 件返します（重複削除）。各エントリに呼び出し回数と最終使用時刻を含みます。コンソールのフィルター下拉が使用し、利用したことのあるモデルのみを表示します。",
        "ko": "호출자가 최근 사용한 모델 ID 최대 50개를 반환합니다(중복 제거). 각 항목에 호출 횟수와 마지막 사용 시간이 포함됩니다. 콘솔 필터 드롭다운이 이를 사용해 실제로 사용한 모델만 표시합니다.",
        "fr": "Renvoie les 50 model_id les plus récemment utilisés par l'appelant (dédupliqués), chacun avec son nombre d'appels et son dernier horodatage. Utilisé par le menu déroulant de filtrage de la console pour n'afficher que les modèles pertinents.",
    },

    "path.get./healthz.summary": {
        "en": "Liveness probe",
        "zh": "存活检测",
        "ja": "稼働確認",
        "ko": "상태 확인",
        "fr": "Sonde de disponibilité",
    },
    "path.get./healthz.description": {
        "en": "Always returns `{\"status\":\"ok\"}` if the process is up. Used by load balancers and uptime monitors.",
        "zh": "进程存活时永远返回 `{\"status\":\"ok\"}`。供负载均衡器和监控工具使用。",
        "ja": "プロセスが稼働している限り常に `{\"status\":\"ok\"}` を返します。ロードバランサーや監視ツールが使用します。",
        "ko": "프로세스가 살아있으면 항상 `{\"status\":\"ok\"}` 를 반환합니다. 로드밸런서 및 가용성 모니터에서 사용합니다.",
        "fr": "Renvoie toujours `{\"status\":\"ok\"}` tant que le processus est en vie. Utilisé par les load balancers et moniteurs.",
    },

    # ─── schema field titles
    "schema.RegisterRequest.email.title":   {"en": "Email", "zh": "邮箱", "ja": "メール", "ko": "이메일", "fr": "E-mail"},
    "schema.RegisterRequest.email.description": {
        "en": "Email address. Used as login identifier and for verification.",
        "zh": "邮箱地址。用作登录身份和邮箱验证。",
        "ja": "メールアドレス。ログイン識別子およびメール認証に使用します。",
        "ko": "이메일 주소. 로그인 식별자 및 이메일 인증에 사용됩니다.",
        "fr": "Adresse e-mail. Sert d'identifiant de connexion et de vérification.",
    },
    "schema.RegisterRequest.password.title": {"en": "Password", "zh": "密码", "ja": "パスワード", "ko": "비밀번호", "fr": "Mot de passe"},
    "schema.RegisterRequest.password.description": {
        "en": "Password (minimum 10 characters).",
        "zh": "密码，至少 10 位。",
        "ja": "パスワード（最低 10 文字）。",
        "ko": "비밀번호(최소 10자).",
        "fr": "Mot de passe (10 caractères minimum).",
    },

    "schema.LoginRequest.email.title": {"en": "Email", "zh": "邮箱", "ja": "メール", "ko": "이메일", "fr": "E-mail"},
    "schema.LoginRequest.password.title": {"en": "Password", "zh": "密码", "ja": "パスワード", "ko": "비밀번호", "fr": "Mot de passe"},

    "schema.ChangePasswordRequest.old_password.title": {
        "en": "Current password", "zh": "当前密码", "ja": "現在のパスワード", "ko": "현재 비밀번호", "fr": "Mot de passe actuel",
    },
    "schema.ChangePasswordRequest.new_password.title": {
        "en": "New password", "zh": "新密码", "ja": "新しいパスワード", "ko": "새 비밀번호", "fr": "Nouveau mot de passe",
    },

    "schema.ForgotPasswordRequest.email.title": {"en": "Email", "zh": "邮箱", "ja": "メール", "ko": "이메일", "fr": "E-mail"},

    "schema.ResetPasswordRequest.token.title": {
        "en": "Reset token", "zh": "重置 token", "ja": "再設定トークン", "ko": "재설정 토큰", "fr": "Token de réinitialisation",
    },
    "schema.ResetPasswordRequest.token.description": {
        "en": "The reset token sent to the user's email by `/auth/forgot-password`. Single-use, expires in 24 hours.",
        "zh": "由 `/auth/forgot-password` 通过邮件发给用户的重置 token。一次性、24 小时过期。",
        "ja": "`/auth/forgot-password` がユーザーのメールに送信した再設定トークン。1 回使い切り、24 時間で失効。",
        "ko": "`/auth/forgot-password` 가 사용자 이메일로 보낸 재설정 토큰. 1회용, 24시간 후 만료.",
        "fr": "Token envoyé par e-mail via `/auth/forgot-password`. Usage unique, expire après 24h.",
    },
    "schema.ResetPasswordRequest.new_password.title": {
        "en": "New password", "zh": "新密码", "ja": "新しいパスワード", "ko": "새 비밀번호", "fr": "Nouveau mot de passe",
    },

    "schema.VerifyEmailRequest.token.title": {
        "en": "Verification token", "zh": "验证 token", "ja": "認証トークン", "ko": "인증 토큰", "fr": "Token de vérification",
    },
    "schema.VerifyEmailRequest.token.description": {
        "en": "Verification token sent to the user's email at registration. Single-use, expires in 24 hours.",
        "zh": "注册时通过邮件发给用户的验证 token。一次性、24 小时过期。",
        "ja": "登録時にユーザーのメールに送信した認証トークン。1 回使い切り、24 時間で失効。",
        "ko": "가입 시 사용자 이메일로 보낸 인증 토큰. 1회용, 24시간 후 만료.",
        "fr": "Token envoyé par e-mail à l'inscription. Usage unique, expire après 24h.",
    },

    "schema.CreateApiKeyRequest.name.title": {
        "en": "Friendly name", "zh": "标识名称", "ja": "識別名", "ko": "표시 이름", "fr": "Nom convivial",
    },
    "schema.CreateApiKeyRequest.name.description": {
        "en": "Optional human-readable label, e.g. `cursor-laptop`. Helps you identify which client is using the key in `/account/api-keys` listings.",
        "zh": "可选标签，例如 `cursor-laptop`。方便在 `/account/api-keys` 列表里识别这条 Key 给哪个客户端用。",
        "ja": "任意の表示名（例：`cursor-laptop`）。`/account/api-keys` 一覧でどのクライアント用かを識別する助けになります。",
        "ko": "선택적 표시 이름(예: `cursor-laptop`). `/account/api-keys` 목록에서 어떤 클라이언트가 쓰는지 식별하는 데 사용됩니다.",
        "fr": "Libellé lisible optionnel, ex. `cursor-laptop`. Aide à identifier quel client utilise la clé dans `/account/api-keys`.",
    },
    "schema.CreateApiKeyRequest.model_whitelist.title": {
        "en": "Model whitelist", "zh": "模型白名单", "ja": "モデルホワイトリスト", "ko": "모델 화이트리스트", "fr": "Liste blanche de modèles",
    },
    "schema.CreateApiKeyRequest.model_whitelist.description": {
        "en": "If non-empty, this key may only call the listed model_ids. Default (empty/null): no restriction — the key may call every model the account has access to.",
        "zh": "若非空，则此 Key 只能调用列表里的 model_id。默认（空/null）= 不限制，可调用账号能访问的全部模型。",
        "ja": "空でない場合、この Key は列挙された model_id のみ呼び出せます。デフォルト（空/null）は制限なし —— アカウントがアクセス可能な全モデルを呼び出せます。",
        "ko": "비어있지 않으면 이 Key 는 나열된 model_id 만 호출할 수 있습니다. 기본값(빈 값/null)은 제한 없음 — 계정이 접근 가능한 모든 모델 호출 가능.",
        "fr": "Si non vide, cette clé ne peut appeler que les model_id listés. Défaut (vide/null) : aucune restriction — accès à tous les modèles du compte.",
    },
    "schema.CreateApiKeyRequest.rate_limit_rpm.title": {
        "en": "Per-key rate limit (RPM)", "zh": "Key 级限速 (RPM)", "ja": "Key 単位レート制限 (RPM)", "ko": "Key별 레이트 제한(RPM)", "fr": "Limite par clé (RPM)",
    },
    "schema.CreateApiKeyRequest.rate_limit_rpm.description": {
        "en": "Requests-per-minute cap for this individual key. If null/omitted the account-tier default is used (60 → 1200 depending on lifetime top-up).",
        "zh": "此 Key 的每分钟请求数上限。若为 null / 未填，则按账户阶梯默认值（60 → 1200，取决于累计充值）。",
        "ja": "この Key の毎分リクエスト数上限。null または未指定の場合、アカウント階層のデフォルト値（累計入金額に応じて 60 → 1200）。",
        "ko": "이 Key 의 분당 요청 수 상한. null 이거나 미지정이면 계정 등급 기본값(누적 충전액에 따라 60 → 1200)이 사용됩니다.",
        "fr": "Plafond requêtes/minute pour cette clé. Si null/omis, on utilise le défaut du palier compte (60 → 1200 selon recharge cumulée).",
    },

    "schema.UpdateApiKeyRequest.name.title": {"en": "Friendly name", "zh": "标识名称", "ja": "識別名", "ko": "표시 이름", "fr": "Nom convivial"},
    "schema.UpdateApiKeyRequest.model_whitelist.title": {"en": "Model whitelist", "zh": "模型白名单", "ja": "モデルホワイトリスト", "ko": "모델 화이트리스트", "fr": "Liste blanche de modèles"},
    "schema.UpdateApiKeyRequest.rate_limit_rpm.title": {"en": "Per-key rate limit (RPM)", "zh": "Key 级限速 (RPM)", "ja": "Key 単位レート制限 (RPM)", "ko": "Key별 레이트 제한(RPM)", "fr": "Limite par clé (RPM)"},
    "schema.UpdateApiKeyRequest.enabled.title": {"en": "Enabled", "zh": "是否启用", "ja": "有効化", "ko": "활성화", "fr": "Activée"},
    "schema.UpdateApiKeyRequest.enabled.description": {
        "en": "Set to false to revoke the key. Same effect as `DELETE /account/api-keys/{id}` but reversible — you can flip it back to true.",
        "zh": "置为 false 即吊销此 Key。效果等同于 `DELETE /account/api-keys/{id}`，但**可撤回** —— 还能改回 true。",
        "ja": "false に設定すると Key を失効させます。`DELETE /account/api-keys/{id}` と同じ効果ですが、**可逆** —— true に戻せます。",
        "ko": "false 로 설정하면 Key 가 폐기됩니다. `DELETE /account/api-keys/{id}` 와 동일하나 **되돌릴 수 있습니다** — true 로 다시 변경 가능.",
        "fr": "Mettre à false révoque la clé. Effet identique à `DELETE /account/api-keys/{id}` mais **réversible** — vous pouvez la remettre à true.",
    },

    "schema.UpdateMeRequest.display_name.title": {"en": "Display name", "zh": "显示名", "ja": "表示名", "ko": "표시 이름", "fr": "Nom affiché"},
    "schema.UpdateMeRequest.avatar_url.title": {"en": "Avatar URL", "zh": "头像 URL", "ja": "アバター URL", "ko": "아바타 URL", "fr": "URL de l'avatar"},

    "schema.TopupIntentRequest.channel.title": {"en": "Channel", "zh": "通道", "ja": "チャネル", "ko": "채널", "fr": "Canal"},
    "schema.TopupIntentRequest.channel.description": {
        "en": "USDC top-up channel: `usdt-trc20` (Tron, recommended for CN), `usdt-sol` (Solana), or `usdt-evm` (BSC/Polygon/Arbitrum/ERC20). The `usdt-` prefix is a legacy database name — we accept USDC tokens.",
        "zh": "USDC 充值通道：`usdt-trc20`（Tron，国内首选）、`usdt-sol`（Solana）、`usdt-evm`（BSC / Polygon / Arbitrum / ERC20）。`usdt-` 前缀是数据库历史命名，实际收的是 USDC token。",
        "ja": "USDC 入金チャネル：`usdt-trc20`（Tron、CN 推奨）、`usdt-sol`（Solana）、`usdt-evm`（BSC / Polygon / Arbitrum / ERC20）。`usdt-` プレフィックスはデータベースの歴史的命名で、実際に受け付けるのは USDC トークンです。",
        "ko": "USDC 충전 채널: `usdt-trc20`(Tron, CN 권장), `usdt-sol`(Solana), `usdt-evm`(BSC / Polygon / Arbitrum / ERC20). `usdt-` 접두사는 DB 호환을 위한 옛 이름이며 실제로는 USDC 토큰을 받습니다.",
        "fr": "Canal de recharge USDC : `usdt-trc20` (Tron, recommandé CN), `usdt-sol` (Solana), `usdt-evm` (BSC / Polygon / Arbitrum / ERC20). Le préfixe `usdt-` est un nom de base de données historique — nous acceptons des tokens USDC.",
    },
    "schema.TopupIntentRequest.amount_usd.title": {"en": "Top-up amount (USD)", "zh": "充值金额（USD）", "ja": "入金額（USD）", "ko": "충전 금액(USD)", "fr": "Montant de la recharge (USD)"},
    "schema.TopupIntentRequest.amount_usd.description": {
        "en": "Top-up amount in USD. Must be > 0 and ≤ 100,000. The actual address-required amount returned by the endpoint will be amended with a 4-digit µ¢ suffix to disambiguate concurrent intents.",
        "zh": "充值金额（USD）。必须大于 0 且 ≤ 100,000。接口返回的实际转账金额会附加 4 位 µ¢ 后缀以区分并发订单。",
        "ja": "入金額（USD）。0 より大きく 100,000 以下。エンドポイントが返す実際の送金金額には 4 桁の µ¢ サフィックスが付与され、同時並行する依頼を区別します。",
        "ko": "충전 금액(USD). 0 초과 100,000 이하. 엔드포인트가 반환하는 실제 송금 금액에는 4자리 µ¢ 접미사가 붙어 동시 진행 요청을 구분합니다.",
        "fr": "Montant de recharge en USD. Doit être > 0 et ≤ 100 000. Le montant exact à envoyer renvoyé par l'endpoint inclut un suffixe µ¢ à 4 chiffres pour distinguer les recharges concurrentes.",
    },
}


def _t(key: str, lang: str) -> str | None:
    """Look up a translation; returns None if missing for this key+lang pair."""
    entry = TRANSLATIONS.get(key)
    if not entry:
        return None
    return entry.get(lang) or entry.get(DEFAULT_LANG)


def build_localized_openapi(app: FastAPI, lang: str) -> dict[str, Any]:
    """Generate the OpenAPI spec, then overlay localized text for `lang`.

    Always returns a deep copy so the cached `app.openapi_schema` is not mutated.
    Falls back to English for any missing translation key.
    """
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG

    # Generate the base spec (FastAPI caches this internally on app.openapi_schema).
    base = app.openapi()
    spec = deepcopy(base)

    # info.title / description
    if title := _t("info.title", lang):
        spec["info"]["title"] = title
    if desc := _t("info.description", lang):
        spec["info"]["description"] = desc

    # tag descriptions (preserve order)
    for tag in spec.get("tags", []):
        translated = _t(f"tag.{tag['name']}.description", lang)
        if translated:
            tag["description"] = translated

    # path × verb summary / description
    for path, ops in spec.get("paths", {}).items():
        for verb, op in ops.items():
            if not isinstance(op, dict):
                continue
            sk = f"path.{verb}.{path}.summary"
            dk = f"path.{verb}.{path}.description"
            if (s := _t(sk, lang)):
                op["summary"] = s
            if (d := _t(dk, lang)):
                op["description"] = d

    # schema property title / description
    schemas = spec.get("components", {}).get("schemas", {})
    for sname, sch in schemas.items():
        for fname, fobj in (sch.get("properties") or {}).items():
            if not isinstance(fobj, dict):
                continue
            tk = f"schema.{sname}.{fname}.title"
            dk = f"schema.{sname}.{fname}.description"
            if (t := _t(tk, lang)):
                fobj["title"] = t
            if (d := _t(dk, lang)):
                fobj["description"] = d

    return spec
