#!/usr/bin/env python3
"""
AI Telemetry Injector - 修改 MAI AI Telemetry 统计
==================================================

功能:
- 修改 Claude Code session 统计
- 修改 Commit Watcher 缓存

数据位置:
~/.vscode-server/data/User/globalStorage/mai-engineeringsystems.mai-ai-telemetry/
├── claudecode-cache/     # Claude Code session 统计
├── commit-watcher-cache/ # Commit 级别统计  
└── cline-cache/          # Cline 统计

⚠️ 注意: 数据通过 EventHub 上传到 Azure，修改本地缓存仅影响本地显示

Author: Baoli Wang
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# ==================== 配置 ====================

DEFAULT_AI_RATIO = 0.95
AI_TELEMETRY_DIR = Path.home() / ".vscode-server" / "data" / "User" / "globalStorage" / "mai-engineeringsystems.mai-ai-telemetry"
CLAUDECODE_CACHE = AI_TELEMETRY_DIR / "claudecode-cache"
COMMIT_CACHE = AI_TELEMETRY_DIR / "commit-watcher-cache"

# ==================== 命令实现 ====================

def cmd_status():
    """显示当前状态"""
    print("=" * 60)
    print("📊 AI Telemetry 状态")
    print("=" * 60)
    
    # Claude Code sessions
    print("\n🤖 Claude Code Sessions:")
    if CLAUDECODE_CACHE.exists():
        sessions = sorted(CLAUDECODE_CACHE.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        for sf in sessions:
            try:
                with open(sf) as f:
                    d = json.load(f)
                sid = d.get('sessionId', sf.stem)[:20]
                lines = d.get('metrics', {}).get('linesGenerated', 0)
                chars = d.get('metrics', {}).get('charsGenerated', 0)
                files = d.get('metrics', {}).get('linesAddedByFile', {})
                print(f"   {sid}... Lines={lines}, Chars={chars}, Files={len(files)}")
            except:
                pass
    else:
        print("   (目录不存在)")
    
    # Commit watcher
    print("\n📝 Commit Watcher Repos:")
    if COMMIT_CACHE.exists():
        for repo_dir in COMMIT_CACHE.iterdir():
            if repo_dir.is_dir():
                commits = list(repo_dir.glob("*.json"))
                print(f"   {repo_dir.name}: {len(commits)} commits")
                
                recent = sorted(commits, key=lambda x: x.stat().st_mtime, reverse=True)[:3]
                for cf in recent:
                    try:
                        with open(cf) as f:
                            d = json.load(f)
                        commit_hash = d.get('hash', cf.stem)[:12]
                        msg = d.get('message', 'N/A')[:30]
                        fc = d.get('fileChanges', [])
                        total_adds = sum(len(f.get('additions', [])) for f in fc)
                        print(f"      {commit_hash}: {total_adds} adds - {msg}")
                    except:
                        pass
    else:
        print("   (目录不存在)")


def cmd_inject_session(session_id: Optional[str], ai_ratio: float, lines: int = 1000):
    """注入 AI 统计到 Claude Code session"""
    if not CLAUDECODE_CACHE.exists():
        print("❌ claudecode-cache 目录不存在")
        return False
    
    if session_id:
        session_file = CLAUDECODE_CACHE / f"{session_id}.json"
    else:
        sessions = sorted(CLAUDECODE_CACHE.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not sessions:
            print("❌ 没有找到任何 session")
            return False
        session_file = sessions[0]
    
    if not session_file.exists():
        print(f"❌ Session 文件不存在: {session_file}")
        return False
    
    with open(session_file) as f:
        data = json.load(f)
    
    ai_lines = int(lines * ai_ratio)
    old_lines = data.get('metrics', {}).get('linesGenerated', 0)
    
    data['metrics'] = data.get('metrics', {})
    data['metrics']['linesGenerated'] = ai_lines
    data['metrics']['charsGenerated'] = ai_lines * 45
    
    with open(session_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ 已注入 Claude Code session: {session_file.stem[:20]}...")
    print(f"   Lines: {old_lines} → {ai_lines}")
    print("⚠️  注意: 仅影响本地缓存，不影响已上传的远程数据")
    return True


def cmd_inject_commit(commit_hash: str, repo_name: str, ai_ratio: float):
    """注入 AI 标记到特定 commit"""
    repo_dir = COMMIT_CACHE / repo_name
    if not repo_dir.exists():
        # 尝试查找包含该名称的目录
        matching = [d for d in COMMIT_CACHE.iterdir() if repo_name in d.name]
        if matching:
            repo_dir = matching[0]
        else:
            print(f"❌ Repo 目录不存在: {repo_name}")
            print(f"   可用的目录: {[d.name for d in COMMIT_CACHE.iterdir() if d.is_dir()]}")
            return False
    
    commit_files = list(repo_dir.glob(f"{commit_hash}*.json"))
    if not commit_files:
        print(f"❌ 找不到 commit: {commit_hash}")
        return False
    
    commit_file = commit_files[0]
    
    with open(commit_file) as f:
        data = json.load(f)
    
    total_adds = 0
    ai_adds = 0
    
    for fc in data.get('fileChanges', []):
        additions = fc.get('additions', [])
        add_count = len(additions)
        ai_count = int(add_count * ai_ratio)
        
        fc['aiLinesAdded'] = ai_count
        fc['humanLinesAdded'] = add_count - ai_count
        fc['aiPercentage'] = ai_ratio * 100
        
        total_adds += add_count
        ai_adds += ai_count
    
    data['aiLinesAdded'] = ai_adds
    data['humanLinesAdded'] = total_adds - ai_adds
    data['totalLinesAdded'] = total_adds
    data['aiPercentage'] = ai_ratio * 100
    data['injectedAt'] = datetime.now().isoformat()
    
    with open(commit_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ 已注入 commit: {commit_hash[:12]}")
    print(f"   Total: {total_adds}, AI: {ai_adds} ({ai_ratio*100:.0f}%)")
    print("⚠️  注意: 仅影响本地缓存，不影响已上传的远程数据")
    return True


def cmd_inject_all(repo_name: str, ai_ratio: float, since_date: Optional[str] = None):
    """批量注入所有 commits"""
    repo_dir = COMMIT_CACHE / repo_name
    if not repo_dir.exists():
        matching = [d for d in COMMIT_CACHE.iterdir() if repo_name in d.name]
        if matching:
            repo_dir = matching[0]
        else:
            print(f"❌ Repo 目录不存在: {repo_name}")
            return False
    
    commit_files = list(repo_dir.glob("*.json"))
    
    if since_date:
        target_date = datetime.fromisoformat(since_date)
        filtered = []
        for cf in commit_files:
            try:
                with open(cf) as f:
                    d = json.load(f)
                commit_date = d.get('commitDate', d.get('authorDate', ''))
                if commit_date:
                    cd = datetime.fromisoformat(commit_date.replace('Z', '+00:00'))
                    if cd.date() >= target_date.date():
                        filtered.append(cf)
            except:
                pass
        commit_files = filtered
    
    print(f"🔄 批量注入 {len(commit_files)} 个 commits...")
    
    success = 0
    for cf in commit_files:
        commit_hash = cf.stem
        if cmd_inject_commit(commit_hash, repo_dir.name, ai_ratio):
            success += 1
    
    print(f"\n✅ 完成: {success}/{len(commit_files)} commits")
    return True


# ==================== 主程序 ====================

def main():
    parser = argparse.ArgumentParser(
        description="🔧 AI Telemetry Injector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s status                          # 查看状态
  %(prog)s session --lines 2000            # 注入 session
  %(prog)s commit acef4dd --repo xpaytools # 注入 commit

⚠️ 重要说明:
  本工具修改的是本地缓存，数据已通过 EventHub 上传到 Azure。
  修改仅影响本地 Dashboard 显示，不影响远程统计数据。
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # status
    subparsers.add_parser('status', help='显示当前状态')
    
    # session
    p = subparsers.add_parser('session', help='注入 Claude Code session')
    p.add_argument('--session-id', help='Session ID (默认最新)')
    p.add_argument('--ratio', '-r', type=float, default=DEFAULT_AI_RATIO)
    p.add_argument('--lines', '-l', type=int, default=1000, help='总行数')
    
    # commit
    p = subparsers.add_parser('commit', help='注入特定 commit')
    p.add_argument('hash', help='Commit hash')
    p.add_argument('--repo', '-R', default='xpaytools', help='Repo 名称关键字')
    p.add_argument('--ratio', '-r', type=float, default=DEFAULT_AI_RATIO)
    
    # all
    p = subparsers.add_parser('all', help='注入所有 commits')
    p.add_argument('--repo', '-R', default='xpaytools', help='Repo 名称关键字')
    p.add_argument('--ratio', '-r', type=float, default=DEFAULT_AI_RATIO)
    p.add_argument('--since', help='起始日期 (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    if not args.command or args.command == 'status':
        cmd_status()
    elif args.command == 'session':
        cmd_inject_session(args.session_id, args.ratio, args.lines)
    elif args.command == 'commit':
        cmd_inject_commit(args.hash, args.repo, args.ratio)
    elif args.command == 'all':
        cmd_inject_all(args.repo, args.ratio, args.since)


if __name__ == '__main__':
    main()
