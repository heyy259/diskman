# Disk Space Manager - 开发日志

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

**商业模式决策**：

| 问题 | 决策 |
|------|------|
| AI 模型选择 | 不固定，根据更新速度选择最新模型 |
| API Key 提供 | 服务端代理，用户无需配置 |

---

### 阶段四：技术实现

**架构设计**：

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  MCP Client │────▶│  API Server │────▶│  AI Models  │
│  (Local)    │     │  (Remote)   │     │  (DeepSeek/ │
│             │     │             │     │   OpenAI)   │
└─────────────┘     └─────────────┘     └─────────────┘
      │
      ▼ Local operations
┌─────────────┐
│   Scanner   │
│   Executor  │
└─────────────┘
```

**实现内容**：

| 模块 | 文件 | 功能 |
|------|------|------|
| Core | `core/scanner.py` | 本地扫描、迁移、链接检测 |
| Client | `client/http_client.py` | HTTP 客户端 SDK |
| Server | `server/api.py` | FastAPI 服务端 |
| AI Service | `server/ai_service.py` | AI 编排服务 |
| Providers | `server/providers/` | DeepSeek、OpenAI 实现 |
| MCP | `mcp_server.py` | MCP 集成 |

**关键代码**：

```python
# AI Provider 抽象
class AIProvider(ABC):
    async def analyze_scan(
        self,
        directories: list[dict],
        user_context: str | None,
        target_drive: str | None,
    ) -> ScanAnalysisResult: ...

# 服务端 API
@app.post("/analyze")
async def analyze_scan(request: AnalyzeRequest):
    result = await ai_service.analyze(...)
    return result

# MCP Tool
@mcp.tool()
async def analyze_with_ai(
    base_path: str | None = None,
    user_context: str | None = None,
    target_drive: str | None = None,
) -> dict:
    # 1. 本地扫描
    # 2. 调用 API 分析
    # 3. 返回结果
```

---

## 当前进度

### 已完成 ✅

- [x] 项目结构重构
- [x] Core 模块（本地扫描/执行）
- [x] AI Provider 抽象层
- [x] DeepSeek Provider 实现
- [x] OpenAI Provider 实现
- [x] 服务端 API（FastAPI）
- [x] 客户端 SDK
- [x] MCP Server 集成
- [x] SKILL.md 更新
- [x] README 更新
- [x] PRD 文档
- [x] 安装测试通过

### 待完成 📋

- [ ] 部署 API 服务到云服务器
- [ ] 配置域名 + HTTPS
- [ ] 添加用户认证
- [ ] 添加计费系统
- [ ] 前端界面（Desktop/Web）
- [ ] 单元测试
- [ ] 文档完善

---

## 运行指南

### 1. 安装

```bash
cd C:\Users\云杨\OneDrive\programing\MAX\trash
pip install -e .
```

### 2. 启动 API 服务

```bash
# 设置 AI Key
export DEEPSEEK_API_KEY=your-deepseek-key

# 启动服务
python -m disk_manager.server.api
```

服务运行在 `http://localhost:8765`

### 3. 启动 MCP 服务

```bash
export DISK_MANAGER_API_URL=http://localhost:8765
python -m disk_manager.mcp_server
```

### 4. OpenCode 集成

在 `opencode.json` 中添加：

```json
{
  "mcpServers": {
    "disk-space-manager": {
      "command": "python",
      "args": ["-m", "disk_manager.mcp_server"],
      "env": {
        "DISK_MANAGER_API_URL": "http://localhost:8765"
      }
    }
  }
}
```

---

## 文件结构

```
C:\Users\云杨\OneDrive\programing\MAX\trash\
├── pyproject.toml              # 项目配置
├── README.md                   # 使用文档
├── SKILL.md                    # OpenCode Skill
├── docs/
│   └── PRD.md                  # 产品需求文档
└── disk_manager/
    ├── __init__.py
    ├── mcp_server.py           # MCP 服务
    ├── core/
    │   ├── __init__.py
    │   └── scanner.py          # 本地扫描/执行
    ├── client/
    │   ├── __init__.py
    │   └── http_client.py      # HTTP 客户端
    └── server/
        ├── __init__.py
        ├── api.py              # FastAPI 端点
        ├── ai_service.py       # AI 编排
        └── providers/
            ├── __init__.py
            ├── base.py         # AI 抽象接口
            ├── deepseek.py     # DeepSeek 实现
            └── openai.py       # OpenAI 实现
```

---

## 下一步计划

1. **短期**：部署 API 服务，完成端到端测试
2. **中期**：添加认证和计费，推出 SaaS 版本
3. **长期**：开发 Desktop 客户端，扩大用户群

---

## 备注

- AI 模型选择策略：不固定一家，根据模型更新速度和效果动态选择
- API Key 由服务端管理，用户无需配置
- 支持本地模式（不调用 AI）和 AI 模式
