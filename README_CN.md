# Diskman

AI 驱动的磁盘空间分析与管理工具。

## 功能特性

- 🔍 **智能扫描** - 分析目录大小，自动检测链接类型（符号链接/Junction）
- 🧠 **智能分析** - 规则引擎 + AI 分析，自动切换分析模式
- 👞 **安全迁移** - 使用符号链接迁移目录到其他磁盘
- 🧹 **智能清理** - 带风险评估的安全清理
- 🤖 **AI 就绪** - 内置 AI 分析能力，支持多种 AI 服务商
- 🔌 **MCP 集成** - 通过 MCP 协议让 AI Agent 自动化管理
- 🔒 **精确统计** - 正确处理符号链接，避免重复计算空间

## 安装

```bash
# 核心功能
pip install diskman

# MCP 支持（用于 AI Agent 集成）
pip install "diskman[mcp]"

# AI 支持（用于 AI 智能分析）
pip install "diskman[ai]"

# 全部安装
pip install "diskman[all]"
```

## 快速开始

### 命令行使用

```bash
# 扫描目录
diskman scan ~/project

# 扫描用户目录，查找大目录
diskman profile

# 分析目录（获取清理/迁移建议）
diskman analyze ~/.cache

# 迁移目录（使用符号链接）
diskman migrate ~/.conda /data/.conda

# 清理目录（默认 dry-run 模式）
diskman clean ~/temp

# 检查链接状态
diskman link ~/.cache
```

### Python API

```python
from diskman import DirectoryScanner, DirectoryAnalyzer, DirectoryMigrator

# 扫描
scanner = DirectoryScanner()
result = scanner.scan_user_profile()

for info in result.directories[:10]:
    print(f"{info.size_mb:.0f} MB - {info.path}")

# 分析
analyzer = DirectoryAnalyzer()
analysis = analyzer.analyze(result.directories[0])

print(f"建议操作: {analysis.recommended_action.value}")
print(f"风险等级: {analysis.risk_level.value}")
print(f"原因: {analysis.reason}")

# 迁移
migrator = DirectoryMigrator()
result = migrator.migrate("~/.conda", "/data/.conda")
```

### AI 智能分析

```python
import asyncio
from diskman import DirectoryScanner, AIService, AIConfig

async def analyze_with_ai():
    # 配置 AI（支持 OpenAI 兼容 API）
    ai = AIService(AIConfig(
        api_key="your-api-key",
        base_url="https://api.deepseek.com",  # 或 OpenAI、通义千问等
        model="deepseek-chat",
    ))
    
    # 扫描
    scanner = DirectoryScanner()
    result = scanner.scan_user_profile()
    
    # AI 分析
    ai_result = await ai.analyze(
        directories=result.directories[:30],
        user_context="我是 Python 开发者",
        target_drive="D:\\",
    )
    
    print(ai_result["summary"])
    for rec in ai_result["recommendations"]:
        print(f"{rec['path']}: {rec['action']} - {rec['reason']}")

asyncio.run(analyze_with_ai())
```

### MCP 集成（用于 AI Agent）

在 MCP 客户端配置中添加：

```json
{
  "mcpServers": {
    "diskman": {
      "command": "diskman-mcp",
      "env": {
        "AI_API_KEY": "your-api-key",
        "AI_BASE_URL": "https://api.deepseek.com",
        "AI_MODEL": "deepseek-chat"
      }
    }
  }
}
```

**可用的 MCP 工具：**

| 工具 | 描述 |
|------|------|
| `scan_directory` | 扫描单个目录 |
| `scan_user_profile` | 扫描用户目录下所有子目录 |
| `check_link_status` | 检查路径链接类型 |
| `analyze_directory` | 规则分析单个目录 |
| `analyze_directories` | 批量智能分析（自动切换 AI/规则模式） |
| `migrate_directory` | 迁移目录并创建符号链接 |
| `clean_directory` | 清理目录内容 |
| `get_ai_provider_info` | 获取 AI 服务状态 |

## 智能分析模式

`analyze_directories` 会自动选择最佳分析方式：

| 条件 | 分析模式 |
|------|----------|
| AI 已配置且可用 | AI 智能分析 |
| 无 AI 配置 / AI 不可用 | 规则引擎分析 |
| AI 分析失败 | 自动降级到规则分析 |

这确保工具始终可用，无论是否有 AI 配置。

## 支持的 AI 服务商

| 服务商 | 配置示例 |
|--------|----------|
| OpenAI | `base_url="https://api.openai.com/v1"` |
| DeepSeek | `base_url="https://api.deepseek.com"` |
| 通义千问 | `base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"` |
| 百度千帆 | `base_url="https://qianfan.baidubce.com/v2/coding"` |
| Kimi/Moonshot | `base_url="https://api.moonshot.cn/v1"` |
| 智谱 GLM | `base_url="https://open.bigmodel.cn/api/paas/v4"` |
| Ollama（本地） | `base_url="http://localhost:11434/v1"` |

## 配置方式

### 参数传入（推荐）

```python
from diskman import AIService, AIConfig

ai = AIService(AIConfig(
    api_key="your-api-key",
    base_url="https://api.deepseek.com",
    model="deepseek-chat",
))
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `AI_API_KEY` 或 `OPENAI_API_KEY` | AI API 密钥 |
| `AI_BASE_URL` 或 `OPENAI_BASE_URL` | API 端点 URL |
| `AI_MODEL` 或 `OPENAI_MODEL` | 模型名称（默认: gpt-4o-mini） |

## 精确的空间统计

Diskman 正确处理符号链接和 Junction：

- **符号链接/Junction**：默认返回 0 大小（数据在目标位置）
- **普通目录**：返回实际大小
- **`count_link_target=True`**：需要时可包含链接目标大小

```python
# 默认：符号链接显示 0 大小（准确反映 C 盘使用情况）
info = scanner.scan_directory("C:\\Users\\you\\LinkedFolder")

# 包含目标大小（用于总数据分析）
info = scanner.scan_directory("C:\\Users\\you\\LinkedFolder", count_link_target=True)
```

## 项目架构

```
diskman/
├── operations/       # 文件系统操作
│   ├── scanner.py   # 目录扫描（含链接检测）
│   ├── migrator.py  # 迁移引擎
│   └── cleaner.py   # 清理引擎
│
├── analysis/         # 智能分析
│   ├── analyzer.py  # 规则引擎分析
│   └── rules/       # 内置规则（40+ 条）
│
├── ai/              # AI 模块
│   ├── service.py   # AI 服务封装
│   └── providers/   # OpenAI 兼容的 Provider
│
├── mcp/             # MCP Server
└── cli.py           # 命令行界面
```

## 使用场景

### 查找大目录

```python
from diskman import DirectoryScanner

scanner = DirectoryScanner()
result = scanner.scan_user_profile()

print(f"总计: {result.total_size_gb:.1f} GB")
for info in result.directories[:20]:
    print(f"{info.size_mb:>8.0f} MB  {info.path}")
```

### 获取清理建议

```python
from diskman import DirectoryScanner, DirectoryAnalyzer

scanner = DirectoryScanner()
analyzer = DirectoryAnalyzer()

result = scanner.scan_user_profile()

for info in result.directories[:10]:
    analysis = analyzer.analyze(info)
    if analysis.recommended_action.value == "can_delete":
        print(f"✓ {info.path}")
        print(f"  {info.size_mb:.0f} MB - {analysis.reason}")
```

### 迁移目录到其他盘

```python
from diskman import DirectoryMigrator

migrator = DirectoryMigrator()

# 将 conda 环境迁移到 D 盘
result = migrator.migrate(
    source=r"C:\Users\you\.conda",
    target=r"D:\migrated\.conda"
)

if result.success:
    print(f"完成！创建了 {result.link_type}")
```

## 许可证

MIT
