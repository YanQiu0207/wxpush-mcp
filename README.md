# wxpush-mcp

wxpush 的 MCP 服务端，将微信推送能力封装为 MCP 工具，供 Claude Desktop、Claude Code 等支持 MCP 协议的客户端直接调用。

**前置条件**：已有一个运行中的 wxpush 服务实例。若尚未部署，参见 [wxpush-py](../wxpush-py)。

## 工具

| 工具名 | 参数 | 说明 |
|---|---|---|
| `send_wechat_message` | `title`、`content`、`shortid` | 发送微信模板消息给指定用户 |
| `check_health` | 无 | 检测 MCP 服务器配置与后端服务是否正常 |

`shortid` 在服务端 `config.toml [users]` 中定义，调用方无需感知 OpenID。

## 快速接入

### 前置条件

已安装 [uv](https://docs.astral.sh/uv/)（`uvx` 随 uv 一起提供）。

### 所需环境变量

| 环境变量 | 说明 |
|---|---|
| `WXPUSH_URL` | wxpush 服务地址，如 `https://your-server.com` |
| `WXPUSH_TOKEN` | API 访问令牌，与服务端 `API_TOKEN` 一致 |

### Claude Code

在 `~/.claude.json` 的 `mcpServers` 中添加：

```json
{
  "mcpServers": {
    "wxpush": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/YanQiu0207/wxpush-mcp",
        "wxpush-mcp"
      ],
      "env": {
        "WXPUSH_URL": "https://your-server.com",
        "WXPUSH_TOKEN": "your-token"
      }
    }
  }
}
```

### Claude Desktop

在 `claude_desktop_config.json` 中添加相同配置：

- macOS：`~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows：`%APPDATA%\Claude\claude_desktop_config.json`

### 验证

配置完成并重启客户端后，调用 `check_health` 工具，正常响应：

```
OK: wxpush service reachable (HTTP 200)
```

## 更新

`uvx` 默认会缓存已安装版本。如需拉取最新代码，在终端执行：

```bash
uv cache clean wxpush-mcp
```

重启客户端后生效。
