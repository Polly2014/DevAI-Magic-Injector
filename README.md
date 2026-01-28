# DevAI-Magic-Injector 🪄

研究和测试 Microsoft AI 代码统计工具的项目。

## 📋 概述

本项目包含两个工具，用于注入和修改 CodeBlend 和 AI Telemetry 的统计数据：

| 工具 | 目标系统 | 数据位置 | 影响范围 |
|------|----------|----------|----------|
| `codeblend_injector.py` | CodeBlend | `~/.codeblend/vscode/` | Pre-commit 可影响上传 |
| `ai_telemetry_injector.py` | MAI AI Telemetry | `metrics_cache.json` | ✅ 可影响远程 (等待自动上传) |

## ⚠️ 重要说明

### 数据流程

```
编辑文件 → 插件记录状态 → Git Commit → 上传到 EventHub (Azure) → Dashboard 显示
                ↑                           ↑
           Pre-commit                  Post-commit
           可影响上传                   仅影响本地
```

### 关键点

1. **Pre-commit Hook**：在 commit 前修改 `document-state.json`，可以影响上传的数据
2. **Post-commit Hook**：在 commit 后修改本地 JSON，仅影响本地 UI 显示
3. **AI Telemetry**：修改 `metrics_cache.json` 后等待自动上传，可影响远程统计 ✅

## 🚀 使用方法

### CodeBlend Injector

```bash
cd src

# 查看状态
python codeblend_injector.py status

# 注入 AI 状态 (commit 前使用，可影响上传)
python codeblend_injector.py inject --ratio 0.95

# 修改已提交的 commit (仅本地显示)
python codeblend_injector.py patch <commit_hash> --ratio 0.95

# 安装 pre-commit hook (推荐)
python codeblend_injector.py install --repo /path/to/repo --type pre

# 安装 post-commit hook (仅本地)
python codeblend_injector.py install --repo /path/to/repo --type post

# 卸载 hook
python codeblend_injector.py uninstall --repo /path/to/repo
```

### AI Telemetry Injector

```bash
cd src

# 查看状态
python ai_telemetry_injector.py status

# 注入 Claude Code session (仅本地)
python ai_telemetry_injector.py session --lines 2000 --ratio 0.95

# 注入特定 commit (仅本地)
python ai_telemetry_injector.py commit <hash> --repo xpaytools

# 批量注入 (仅本地)
python ai_telemetry_injector.py all --repo xpaytools --since 2026-01-20
```

## 📁 项目结构

```
DevAI-Magic-Injector/
├── README.md              # 本文档
├── src/
│   ├── codeblend_injector.py     # CodeBlend 注入器
│   └── ai_telemetry_injector.py  # AI Telemetry 注入器
├── docs/
│   └── ARCHITECTURE.md    # 架构说明
├── tests/                 # 测试文件
└── examples/              # 示例脚本
```

## 🔬 数据目录

### CodeBlend
```
~/.codeblend/vscode/
├── sessions/<session>/
│   └── document-state.json    # 行级别状态: 0=未改, 1=Human, 2=AI
└── repo/<repo>/commits/
    └── <hash>.json            # Commit 统计
```

### AI Telemetry
```
~/.vscode-server/data/User/globalStorage/mai-engineeringsystems.mai-ai-telemetry/
├── claudecode-cache/          # Claude Code session
├── commit-watcher-cache/      # Commit 级别统计
└── cline-cache/               # Cline 统计
```

## 📝 License

MIT - 仅供研究和学习使用
