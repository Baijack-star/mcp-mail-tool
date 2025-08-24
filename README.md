# MCP Mail Tool MVP

一个基于 Model Context Protocol (MCP) 的邮件工具，支持通过 IMAP/SMTP 协议访问 Outlook/Office365 邮箱，作为浏览器邮箱访问的替代方案。

## 🚀 功能特性

- **邮件读取** (`mail_read`): 从指定文件夹读取最新邮件，返回发件人、主题、时间、正文摘要和邮件ID
- **邮件发送** (`mail_send`): 通过SMTP发送邮件，支持纯文本格式
- **邮件详情** (`mail_get`): 根据邮件ID获取完整邮件内容
- **错误处理**: 自动重试机制，支持登录失败、网络错误等异常处理
- **配置管理**: 通过JSON文件管理邮箱配置

## 📋 系统要求

- Python 3.7+
- 网络连接
- Outlook/Office365 邮箱账号

## 🛠️ 安装配置

### 1. 克隆仓库

```bash
git clone https://github.com/Baijack-star/mcp-mail-tool.git
cd mcp-mail-tool
```

### 2. 配置邮箱认证

复制配置模板并填入您的邮箱信息：

```bash
cp config.json config_local.json
```

编辑 `config_local.json`：

```json
{
  "email": "your-email@outlook.com",
  "password": "your-app-password",
  "imap_server": "outlook.office365.com",
  "imap_port": 993,
  "smtp_server": "smtp.office365.com",
  "smtp_port": 587,
  "use_ssl": true,
  "retry_count": 3,
  "retry_delay": 2
}
```

### 3. Outlook 邮箱认证设置

**重要**: 对于 Outlook/Office365 邮箱，强烈建议使用应用密码而非常规密码。

#### 生成应用密码步骤：

1. 登录 [Microsoft 账户安全页面](https://account.microsoft.com/security)
2. 选择 "高级安全选项"
3. 在 "应用密码" 部分，点击 "创建新的应用密码"
4. 为应用密码命名（如 "MCP Mail Tool"）
5. 复制生成的密码到配置文件的 `password` 字段

#### 启用必要设置：

- 确保启用了 "安全性较低的应用访问" 或使用应用密码
- 如果启用了双重验证，必须使用应用密码

## 📖 使用说明

### 命令行使用

#### 读取邮件

```bash
# 读取收件箱最新10封邮件
python mcp_mail.py read

# 读取指定文件夹的邮件
python mcp_mail.py read "Sent Items" 5

# 读取更多邮件
python mcp_mail.py read INBOX 20
```

#### 发送邮件

```bash
python mcp_mail.py send "recipient@example.com" "测试主题" "邮件正文内容"
```

#### 获取邮件详情

```bash
# 使用从 mail_read 获取的邮件ID
python mcp_mail.py get "12345"
```

### Python API 使用

```python
from mcp_mail import MCPMailTool

# 初始化工具
tool = MCPMailTool("config_local.json")

# 读取邮件
result = tool.mail_read(folder="INBOX", limit=10)
print(result)

# 发送邮件
result = tool.mail_send(
    to="recipient@example.com",
    subject="测试邮件",
    body="这是一封测试邮件"
)
print(result)

# 获取邮件详情
result = tool.mail_get("12345")
print(result)
```

### MCP 接口集成

本工具符合 MCP 标准，可以直接集成到支持 MCP 的 AI 系统中。接口定义请参考 `mail.mcp.json` 文件。

## 📊 返回数据格式

### mail_read 返回格式

```json
{
  "success": true,
  "emails": [
    {
      "id": "12345",
      "subject": "邮件主题",
      "sender": "sender@example.com",
      "date": "Mon, 19 Dec 2024 10:30:00 +0000",
      "body_summary": "邮件正文摘要..."
    }
  ],
  "count": 1
}
```

### mail_send 返回格式

```json
{
  "success": true,
  "message": "Email sent to recipient@example.com",
  "timestamp": "2024-12-19T10:30:00.123456"
}
```

### mail_get 返回格式

```json
{
  "success": true,
  "id": "12345",
  "subject": "邮件主题",
  "sender": "sender@example.com",
  "to": "recipient@example.com",
  "date": "Mon, 19 Dec 2024 10:30:00 +0000",
  "body": "完整的邮件正文内容"
}
```

## ⚠️ 错误码说明

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `IMAP_CONNECTION_FAILED` | IMAP服务器连接失败 | 检查网络连接和服务器配置 |
| `SMTP_CONNECTION_FAILED` | SMTP服务器连接失败 | 检查网络连接和服务器配置 |
| `AUTHENTICATION_FAILED` | 邮箱认证失败 | 检查邮箱地址和密码，建议使用应用密码 |
| `FOLDER_NOT_FOUND` | 指定的邮件文件夹不存在 | 检查文件夹名称是否正确 |
| `EMAIL_NOT_FOUND` | 指定ID的邮件不存在 | 检查邮件ID是否有效 |
| `INVALID_EMAIL_FORMAT` | 邮箱地址格式无效 | 检查邮箱地址格式 |
| `NETWORK_ERROR` | 网络连接错误 | 检查网络连接，工具会自动重试3次 |
| `CONFIGURATION_ERROR` | 配置文件错误 | 检查配置文件格式和必填字段 |
| `ENCODING_ERROR` | 邮件编码错误 | 邮件内容编码问题，请联系技术支持 |

## 🔧 故障排除

### 常见问题

1. **认证失败**
   - 确保使用应用密码而非常规密码
   - 检查是否启用了双重验证
   - 验证邮箱地址和密码是否正确

2. **连接超时**
   - 检查网络连接
   - 确认防火墙设置
   - 尝试增加重试次数

3. **邮件读取失败**
   - 检查文件夹名称（区分大小写）
   - 确认邮箱中有邮件
   - 检查IMAP是否启用

4. **邮件发送失败**
   - 检查收件人邮箱地址
   - 确认SMTP设置正确
   - 检查邮件内容是否包含敏感信息

### 调试模式

启用详细日志记录：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔒 安全注意事项

- 不要将包含真实密码的配置文件提交到版本控制系统
- 使用应用密码而非主密码
- 定期更换应用密码
- 在生产环境中使用加密存储凭据

## 📝 开发信息

- **版本**: 1.0.0
- **作者**: AI-Dev
- **许可证**: MIT
- **仓库**: https://github.com/Baijack-star/mcp-mail-tool

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个工具。

## 📄 许可证

MIT License - 详见 LICENSE 文件

---

**注意**: 这是一个 MVP（最小可行产品）版本，专注于核心邮件收发功能。未来版本将支持附件处理、HTML邮件、邮件搜索等高级功能。
