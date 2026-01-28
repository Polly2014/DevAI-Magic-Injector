# 架构说明

## CodeBlend 数据流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     CodeBlend 数据流程                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. VS Code 中编辑文件                                          │
│     ↓                                                           │
│  2. CodeBlend 扩展实时跟踪每行状态                               │
│     → 存储到 ~/.codeblend/vscode/sessions/<session>/            │
│       document-state.json                                       │
│     • 状态码: 0=未修改, 1=Human, 2=AI (来自 Chat 粘贴)           │
│     ↓                                                           │
│  3. Git Commit 时                                               │
│     → CodeBlend 读取 document-state.json                        │
│     → 生成 commit JSON 并上传到 EventHub                         │
│     → 清空当前文件状态                                           │
│     ↓                                                           │
│  4. 本地存储                                                     │
│     → ~/.codeblend/vscode/repo/<repo>/commits/<hash>.json       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 注入时机对比

### Pre-Commit (推荐 ✅)

```
编辑文件 → document-state.json 
                    ↓
              ⭐ Pre-Commit Hook
              修改 document-state.json
                    ↓
              Git Commit
                    ↓
              CodeBlend 读取修改后的状态
                    ↓
              生成 commit JSON → 上传到 EventHub ✅
                    ↓
              Dashboard 显示正确数据 ✅
```

**优点**: 可以影响上传到云端的数据

### Post-Commit (仅本地 ⚠️)

```
编辑文件 → Git Commit
                    ↓
              CodeBlend 读取原始状态
                    ↓
              生成 commit JSON → 上传到 EventHub (原始数据)
                    ↓
              ⭐ Post-Commit Hook
              修改本地 commit JSON
                    ↓
              本地 UI 显示修改后数据 ✅
              远程 Dashboard 显示原始数据 ❌
```

**缺点**: 只能影响本地显示

## AI Telemetry 数据流程 (验证有效 ✅)

```
┌─────────────────────────────────────────────────────────────────┐
│                   AI Telemetry 数据流程                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 使用 Claude Code / Copilot / Cline 等工具                   │
│     ↓                                                           │
│  2. MAI AI Telemetry 扩展记录到 metrics_cache.json              │
│     ↓                                                           │
│  ⭐ 【修改窗口】在此修改缓存文件                                   │
│     ↓                                                           │
│  3. 插件定期读取缓存并上传到 EventHub                            │
│     → 数据发送到 Azure                                          │
│     ↓                                                           │
│  4. Dashboard 显示更新后的数据 ✅                                │
│                                                                 │
│  关键: 缓存文件是数据源，修改后等待自动上传即可生效               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 文件格式

### document-state.json

```json
{
  "/path/to/file.py": [0, 0, 1, 1, 2, 2, 2, 1, 0],
  "/path/to/other.js": [2, 2, 2, 1, 1, 0, 0]
}
```

- 数组索引 = 行号
- `0` = 未修改
- `1` = Human 修改
- `2` = AI 生成 (从 Chat 粘贴)

### commit JSON

```json
{
  "commit": "abc123...",
  "totalChanged": 100,
  "ai": 95,
  "human": 5,
  "aiCommit": true,
  "files": [
    {
      "path": "/path/to/file.py",
      "totalChanged": 50,
      "ai": 48,
      "human": 2,
      "aiPercentage": 96.0
    }
  ]
}
```
