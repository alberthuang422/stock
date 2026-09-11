# MCP 多机配置指南

> 目的：在另一台电脑（如 Mac mini）复现本机的 MCP 连接器配置。
> ⚠️ 本仓库为 **public**，本文档只写「如何配」，不写任何真实密钥。真实 key 见本机 `~/.workbuddy/mcp.json`（勿提交）。

## 一、核心结论（先看这个）

| MCP | 认证方式 | 有无静态 key | 跨机复制方式 |
|---|---|---|---|
| **futu-mcp** | OAuth 2.0（公共客户端，无 secret） | ❌ 无 | 加 URL 后走连接器中心重新授权 |
| jin10 | HTTP + Bearer Token | ✅ 有 | 复制 `Authorization` header |
| hithink-finance-*（4 个） | HTTP + API Key | ✅ 有 | 复制 `X-api-key` header |

- **富途没有可复制粘贴的静态凭证**。它的 access_token / refresh_token 是 OAuth 动态签发、用 aes-256-gcm 加密存在本机、且 `client_id` 与回环回调地址 `127.0.0.1:59407/oauth/callback` 都绑定单台机器，token 仅 2 小时有效。
- 所以富途必须在目标机器**重新走一遍授权**（30 秒内完成，见下文）。

## 二、富途（futu-mcp）——重新授权法

1. 在目标机器的 `~/.workbuddy/mcp.json` 的 `mcpServers` 下加：

```json
"futu-mcp": {
  "url": "https://mcp.futunn.com/mcp",
  "disabled": false
}
```

2. 打开 WorkBuddy → 右上角**连接器中心** → 找到 `futu-mcp` → 点「信任 / 启用」。
3. 弹出富途 OAuth 授权页，用你的富途账号登录并授权。
4. 完成后目标机器自动完成动态客户端注册 + 令牌落地。

授权范围：`quote:read` `quote:write`（两个牛牛账号 accid）。成功后即可用 `quote_history_kline` 等富途行情工具。

**补充**：富途 access_token 仅 2 小时有效，本仓库 `scripts/futu_token_refresh.py` 负责用 refresh_token 自动续期（token 端点 `https://webapi.futunn.com/oauth2/token`，认证方式为「none」，无需 client_secret）。

## 三、jin10 —— 复制 Bearer Token

目标机器 `mcp.json` 加：

```json
"jin10": {
  "type": "http",
  "url": "https://mcp.jin10.com/mcp",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer <本机 mcp.json 中的 token>"
  }
}
```

## 四、hithink-finance（A股 / 指数 / meta / 基金）—— 复制 API Key

4 个服务共用同一个 `X-api-key`，目标机器 `mcp.json` 加：

```json
"hithink-finance-a-share": {
  "type": "http",
  "url": "https://fuyao.aicubes.cn/mcp/a-share",
  "headers": { "X-api-key": "<本机 mcp.json 中的 key>" }
},
"hithink-finance-a-share-index": {
  "type": "http",
  "url": "https://fuyao.aicubes.cn/mcp/a-share-index",
  "headers": { "X-api-key": "<同上>" }
},
"hithink-finance-meta": {
  "type": "http",
  "url": "https://fuyao.aicubes.cn/mcp/meta",
  "headers": { "X-api-key": "<同上>" }
},
"hithink-finance-fund": {
  "type": "http",
  "url": "https://fuyao.aicubes.cn/mcp/fund",
  "headers": { "X-api-key": "<同上>" }
}
```

## 五、安全提示

- 目标机器的授权 / token 落地后在 WorkBuddy 里正常使用即可，**不要**把真实 key 写进这个 public 仓库。
- 已发现本仓库 `Temp/` 目录有富途 `client_id`、`accid`（牛牛账号 ID）历史随提交暴露在 public remote。这些不构成直接登录凭据（无 secret、token 已过期），但建议后续把 `Temp/` 加入 `.gitignore` 并清理历史，如需要可另行处理。