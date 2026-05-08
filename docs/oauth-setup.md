# OAuth 一键登录配置（GitHub + Google）

> 状态：v0.2 · 2026-05-08
> 这个文档帮你 10 分钟内开通 GitHub 和 Google 一键登录。

---

## 0. 你需要做的事 vs 系统自动做的事

| 步骤 | 谁做 |
|---|---|
| 在 GitHub / Google Console 创建 OAuth App | **你**（一次性，5 分钟） |
| 把 client_id + client_secret 加到 Prism | **CLI 一行命令**（自动写 `.env` + 重启服务） |
| 验证：登录页出现 GitHub / Google 按钮 | **你**（开浏览器看一眼） |

---

## 1. GitHub OAuth App

### 1.1 创建

1. 登录 GitHub，打开 <https://github.com/settings/applications/new>
2. 填表：
   - **Application name**: `Prism`
   - **Homepage URL**: `https://www.ai100trading.cn`
   - **Application description**: （可选）`Transparent AI gateway`
   - **Authorization callback URL**: `https://www.ai100trading.cn/suanli-api/auth/oauth/github/callback`
3. 点 **Register application**
4. 进入新建的 App 详情页，记下 **Client ID**（一串 20 字符）
5. 点 **Generate a new client secret** → 立刻复制（关掉就再也看不到了）

### 1.2 配进 Prism

SSH 到服务器：

```bash
ssh ubuntu@43.156.207.26
cd /opt/prism
.venv/bin/prism-admin oauth set \
  --provider github \
  --client-id "Iv1.xxxxxxxxxxxxxxx" \
  --client-secret "ghs_xxxxxxxxxxxxxxxxxxxxxxxxxx"
```

或者把 ID/Secret 发给我，我帮你执行。

---

## 2. Google OAuth Client

### 2.1 创建

1. 进 <https://console.cloud.google.com/apis/credentials>
2. 顶部 project 选你已有项目，没有就新建一个（项目名随意，例如 `prism`）
3. 进 **APIs & Services → OAuth consent screen**：
   - User type: **External**
   - App name: `Prism`
   - User support email: 你的邮箱
   - Developer contact: 你的邮箱
   - Save & Continue 一路下去（无需上传 logo / 隐私政策，Testing 模式即可）
4. 回 **Credentials → + CREATE CREDENTIALS → OAuth client ID**
   - Application type: **Web application**
   - Name: `Prism web`
   - **Authorized redirect URIs**: 加一条
     `https://www.ai100trading.cn/suanli-api/auth/oauth/google/callback`
   - 创建 → 弹出 client_id + client_secret，复制保存

### 2.2 配进 Prism

```bash
.venv/bin/prism-admin oauth set \
  --provider google \
  --client-id "1234567890-xxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com" \
  --client-secret "GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx"
```

---

## 3. 验证

1. 命令执行后系统会**自动重启 prism 服务**
2. 浏览器打开 <https://www.ai100trading.cn/login>
3. 表单下方应该出现 **使用 GitHub 继续** + **使用 Google 继续** 两个按钮
4. 点一下 → 跳到 GitHub/Google 授权页 → 同意 → 跳回 Prism 控制台 → 自动登录

如果按钮没出现，看 systemd 日志确认配置加载：
```bash
sudo journalctl -u prism -n 50 --no-pager
```

---

## 4. 测试模式 vs 公开模式（Google）

刚创建的 Google OAuth 默认在 **Testing** 模式，只允许你预先添加的"Test users"登录。要让任意用户登录：
- **OAuth consent screen → Publishing status → PUBLISH APP** → 提交审核（小项目 < 100 用户的请求一般 1-2 周内通过；如果要求 sensitive scopes 才需要更严格审核）

GitHub 没有这个限制，立即对所有 GitHub 账号开放。

---

## 5. 不打开 OAuth 也能用？

**能**。不配 OAuth 时：
- 登录页只显示邮箱密码表单（OAuth 按钮自动隐藏）
- 用户走标准注册 → 邮件验证 → 登录路径
- 体验稍差但功能完整

OAuth 是"锦上添花"——主要好处是用户少打一个密码 + 减少忘记密码的麻烦。
