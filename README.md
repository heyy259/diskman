# Diskman

AI-ready disk space analysis and management.

## Features

- 🔍 **Smart Scan** - Analyze directory sizes with file type detection
- 🧠 **Intelligent Analysis** - Rule-based recommendations for cleanup/migration
- 🔄 **Safe Migration** - Move directories using symbolic links
- 🧹 **Smart Clean** - Safe cleanup with risk evaluation
- 🤖 **AI-Ready** - MCP integration for AI agent automation
- 🔌 **Modular Design** - Use operations, analysis, or AI separately

## Install

```bash
# Core functionality
pip install diskman

# With MCP support (for AI agents)
pip install "diskman[mcp]"

# With everything
pip install "diskman[all]"
```

## Quick Start

### CLI Usage

```bash
# Scan directory
diskman scan ~/project

# Scan user profile for large directories
diskman profile

# Analyze a directory (get recommendations)
diskman analyze ~/.cache

# Migrate directory with symbolic link
diskman migrate ~/.conda /data/.conda

# Clean directory (dry run by default)
diskman clean ~/temp
```

### Python API

```python
from diskman import DirectoryScanner, DirectoryAnalyzer, DirectoryMigrator

# Scan
scanner = DirectoryScanner()
result = scanner.scan_user_profile()

for info in result.directories[:10]:
    print(f"{info.size_mb:.0f} MB - {info.path}")

# Analyze
analyzer = DirectoryAnalyzer()
analysis = analyzer.analyze(result.directories[0])

print(f"Action: {analysis.recommended_action.value}")
print(f"Risk: {analysis.risk_level.value}")
print(f"Reason: {analysis.reason}")

# Migrate
migrator = DirectoryMigrator()
result = migrator.migrate("~/.conda", "/data/.conda")
```

### MCP Integration (for AI Agents)

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "diskman": {
      "command": "diskman-mcp"
    }
  }
}
```

Or with custom API endpoint:

```json
{
  "mcpServers": {
    "diskman": {
      "command": "diskman-mcp",
      "env": {
        "DISKMAN_API_URL": "https://your-api.example.com",
        "DISKMAN_API_KEY": "your-key"
      }
    }
  }
}
```

## Architecture

```
diskman/
├── operations/       # File system operations (scan, migrate, clean)
│   ├── scanner.py
│   ├── migrator.py
│   └── cleaner.py
│
├── analysis/         # Directory analysis and recommendations
│   ├── analyzer.py
│   └── rules/        # Built-in analysis rules
│
├── ai/              # AI-powered analysis (optional)
│   ├── service.py
│   └── providers/   # DeepSeek, OpenAI, etc.
│
├── api/             # HTTP API (optional)
├── mcp/             # MCP server (for AI agents)
└── cli.py           # Command-line interface
```

## Two Core Modules

### Operations Core (Execution Layer)

Handles file system operations safely:

- **Scanner**: Calculate directory sizes, detect link types
- **Migrator**: Move directories and create symbolic links
- **Cleaner**: Safe deletion with protection for critical paths

### Analysis Core (Decision Layer)

Provides intelligent recommendations:

- **Rule Engine**: 40+ built-in rules for common directories
- **Heuristics**: Pattern-based analysis for unknown directories
- **Risk Assessment**: Safe/low/medium/high/critical ratings
- **Action Recommendations**: can_delete, can_move, keep, review

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DISKMAN_API_URL` | API server URL (for MCP client) |
| `DISKMAN_API_KEY` | API key (optional) |
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `AI_DEFAULT_PROVIDER` | Default AI provider (deepseek/openai) |

## Examples

### Find large directories

```python
from diskman import DirectoryScanner

scanner = DirectoryScanner()
result = scanner.scan_user_profile()

print(f"Total: {result.total_size_gb:.1f} GB")
for info in result.directories[:20]:
    print(f"{info.size_mb:>8.0f} MB  {info.path}")
```

### Get cleanup recommendations

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

### Migrate a directory

```python
from diskman import DirectoryMigrator

migrator = DirectoryMigrator()

# Move conda environment to D drive
result = migrator.migrate(
    source=r"C:\Users\you\.conda",
    target=r"D:\migrated\.conda"
)

if result.success:
    print(f"Done! Created {result.link_type}")
```

## License

MIT
