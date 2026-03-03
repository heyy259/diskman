# Diskman - 开发日志

> 记录产品设计讨论和开发进度

---

## 2026-02-28

### 阶段一：Skill 设计

**起点**：用户有一个 SKILL.md，用于管理磁盘空间，包含：
- 扫描目录大小
- 检查链接状态（Symbolic Link / Junction）
- 迁移目录到其他盘

**问题**：这个 skill 依赖大模型理解自然语言指令，每次执行都需要大模型推理，结果不稳定。

---

### 阶段二：产品化讨论

**用户提问**：如何把 skill 做成产品？

**分析**：

| 现状 | 问题 |
|------|------|
| SKILL.md 是"提示词" | 依赖大模型理解，结果不可预期 |
| 每步都需要模型决策 | Token 消耗大，响应慢 |
| 依赖上下文理解 | 难以标准化 |

**解决方案**：将"如何执行"解耦成工具层

```
当前模式：
User → 大模型 → 理解指令 → 推理每步操作 → 执行（不稳定）

产品化模式：
User → 大模型 → 识别意图 → 调用工具 → 返回结果（稳定）
                     ↑
              SKILL.md 只负责"何时用"
              工具负责"怎么做"
```

---

### 阶段三：产品需求设计

创建 PRD 文档，定义：

**产品线**：
```
CLI → MCP → Desktop → Web → SDK
```

**核心功能**：
- 智能扫描模块
- AI 分析模块
- 建议展示模块
- 执行模块

---

### 阶段四：技术实现

**架构设计**（简化版）：

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Server / Python API              │
│                                                         │
│   analyze_directories() ──→ AIService ──→ AI Provider   │
│                                    │                    │
│                                    ├─→ OpenAI           │
│                                    ├─→ DeepSeek         │
│                                    ├─→ Qwen             │
│                                    └─→ Ollama (本地)    │
│                                                         │
│   配置：参数传入 或 环境变量 AI_API_KEY / AI_BASE_URL   │
└─────────────────────────────────────────────────────────┘
```

---

## 当前进度

### 已完成 ✅

- [x] 项目结构重构
- [x] Operations 模块（本地扫描/迁移/清理）
- [x] Analysis 模块（规则引擎 + 启发式分析）
- [x] AI Provider 抽象层
- [x] OpenAI Provider 实现
- [x] MCP Server 集成（直接调用 AI，无需 API Server）
- [x] CLI 命令
- [x] 数据模型（models.py）
- [x] README 更新
- [x] PRD 文档
- [x] 安装测试通过
- [x] 单元测试
- [x] AI 配置参数传入支持
- [x] 智能分析模式自动切换

### 待完成 📋

- [ ] 前端界面（Desktop/Web）
- [ ] 文档完善

---

## 运行指南

### 1. 安装

```bash
pip install -e .

# 或从 PyPI 安装
pip install diskman

# 安装可选依赖
pip install "diskman[mcp]"   # MCP 支持
pip install "diskman[ai]"    # AI 支持
pip install "diskman[all]"   # 全部
```

### 2. CLI 使用

```bash
# 扫描目录
diskman scan ~/project

# 扫描用户配置文件目录
diskman profile

# 分析目录
diskman analyze ~/.cache

# 迁移目录
diskman migrate ~/.conda /data/.conda

# 清理目录
diskman clean ~/temp

# 检查链接状态
diskman link ~/.cache
```

### 3. Python API 使用

```python
from diskman import DirectoryScanner, DirectoryAnalyzer, AIService, AIConfig

# 扫描
scanner = DirectoryScanner()
result = scanner.scan_user_profile()

# 规则分析
analyzer = DirectoryAnalyzer()
analysis = analyzer.analyze(result.directories[0])

# AI 分析（可选）
ai = AIService(AIConfig(
    api_key="your-api-key",
    base_url="https://api.deepseek.com",
    model="deepseek-chat",
))
```

### 4. MCP 集成

```bash
# 启动 MCP 服务（使用环境变量配置）
export AI_API_KEY=your-api-key
export AI_BASE_URL=https://api.deepseek.com
diskman-mcp
```

在 MCP 客户端配置：

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

---

## 文件结构

```
diskman/
├── __init__.py              # 包入口，导出主要类
├── models.py                # 数据模型（DirectoryInfo, AnalysisResult 等）
├── cli.py                   # CLI 命令入口
│
├── operations/              # 文件系统操作
│   ├── __init__.py
│   ├── scanner.py           # 目录扫描
│   ├── migrator.py          # 目录迁移
│   └── cleaner.py           # 目录清理
│
├── analysis/                # 智能分析
│   ├── __init__.py
│   ├── analyzer.py          # 分析器
│   └── rules/               # 规则引擎
│       ├── __init__.py
│       ├── engine.py        # 规则引擎核心
│       └── builtin.py       # 内置规则（40+ 条）
│
├── ai/                      # AI 分析（可选）
│   ├── __init__.py
│   ├── service.py           # AI 服务编排
│   └── providers/           # AI 提供商
│       ├── __init__.py
│       ├── base.py          # 抽象基类
│       └── openai.py        # OpenAI 兼容实现
│
└── mcp/                     # MCP 服务（可选）
    ├── __init__.py
    └── server.py            # MCP Server
```

---

## 核心模块

### Operations Core（执行层）

安全的文件系统操作：

| 类 | 功能 |
|---|------|
| `DirectoryScanner` | 计算目录大小、检测链接类型 |
| `DirectoryMigrator` | 移动目录并创建符号链接 |
| `DirectoryCleaner` | 安全删除（带保护机制） |

### Analysis Core（决策层）

智能推荐系统：

| 组件 | 功能 |
|------|------|
| `DirectoryAnalyzer` | 分析目录并给出建议 |
| `RuleEngine` | 40+ 内置规则 |
| 启发式分析 | 处理未知目录类型 |

**输出**：
- 目录类型（cache/dependency/build/temp/...）
- 风险等级（safe/low/medium/high/critical）
- 推荐操作（can_delete/can_move/keep/review）
- 置信度（0.0-1.0）

### AI Module（可选增强）

当规则不足以判断时，使用 AI 增强：

- 支持 OpenAI 兼容 API（OpenAI、DeepSeek、Qwen、Ollama 等）
- 自动切换分析模式：有 AI 配置用 AI，无配置用规则
- 配置方式：参数传入 或 环境变量

---

## 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_scanner.py -v
pytest tests/test_analyzer.py -v
```

---

## 下一步计划

1. **短期**：完善文档，提升用户体验
2. **中期**：开发 Desktop 客户端
3. **长期**：推出 Web 版本，扩大用户群

---

## 备注

- AI 模型选择策略：支持任意 OpenAI 兼容 API，用户可自由选择
- AI 配置：支持参数传入（推荐）或环境变量
- 本地优先：无 AI 配置时自动使用规则引擎分析
