#!/usr/bin/env python3
"""
CodeBlend Injector - 修改 CodeBlend AI 统计
============================================

功能:
- 修改 document-state.json (pre-commit，可影响上传数据)
- 修改 commit JSON (post-commit，仅影响本地显示)

数据位置:
- ~/.codeblend/vscode/sessions/<session>/document-state.json
- ~/.codeblend/vscode/repo/<repo>/commits/<hash>.json

Author: Baoli Wang
"""

import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ==================== 配置 ====================

DEFAULT_AI_RATIO = 0.95
CODEBLEND_BASE = Path.home() / ".codeblend" / "vscode"
SESSIONS_DIR = CODEBLEND_BASE / "sessions"
REPO_DIR = CODEBLEND_BASE / "repo"

# ==================== 核心工具函数 ====================

def get_latest_session() -> Optional[Path]:
    """获取最新的 CodeBlend session 目录"""
    if not SESSIONS_DIR.exists():
        return None
    sessions = sorted(SESSIONS_DIR.glob("*"), key=lambda x: x.name, reverse=True)
    return sessions[0] if sessions else None


def load_document_state(session: Path) -> Dict:
    """加载 document-state.json"""
    state_path = session / "document-state.json"
    if state_path.exists():
        with open(state_path, 'r') as f:
            return json.load(f)
    return {}


def save_document_state(session: Path, state: Dict):
    """保存 document-state.json"""
    state_path = session / "document-state.json"
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)


def get_staged_files(repo_path: str) -> List[str]:
    """获取 git staged 的文件列表"""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return [os.path.join(repo_path, f) for f in result.stdout.strip().split('\n') if f]
    except Exception:
        pass
    return []


def get_latest_commit_hash(repo_path: str) -> Optional[str]:
    """获取最新 commit hash"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


# ==================== 注入功能 ====================

def inject_file_state(state: Dict, file_path: str, ai_ratio: float) -> bool:
    """
    注入单个文件的 AI 状态
    状态码: 0=未修改, 1=Human, 2=AI
    """
    if file_path not in state:
        return False
    
    lines = state[file_path]
    total = len(lines)
    if total == 0:
        return False
    
    # 将前 ai_ratio 比例的行标记为 AI
    ai_count = int(total * ai_ratio)
    state[file_path] = [2 if i < ai_count else 1 for i in range(total)]
    return True


def inject_all_state(state: Dict, ai_ratio: float) -> int:
    """注入所有文件的 AI 状态"""
    count = 0
    for file_path in list(state.keys()):
        if inject_file_state(state, file_path, ai_ratio):
            count += 1
    return count


def patch_commit_json(commit_file: Path, ai_ratio: float) -> bool:
    """修改 commit JSON 文件"""
    try:
        with open(commit_file, 'r') as f:
            data = json.load(f)
        
        total = data.get('totalChanged', 0)
        if total == 0:
            return False
        
        new_ai = int(total * ai_ratio)
        new_human = total - new_ai
        
        data['ai'] = new_ai
        data['human'] = new_human
        data['aiCommit'] = True
        
        # 修改文件级别
        for f_data in data.get('files', []):
            f_total = f_data.get('totalChanged', 0)
            f_data['ai'] = int(f_total * ai_ratio)
            f_data['human'] = f_total - f_data['ai']
            f_data['aiPercentage'] = ai_ratio * 100
        
        with open(commit_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return False


# ==================== 命令实现 ====================

def cmd_status():
    """显示当前状态"""
    print("=" * 60)
    print("📊 CodeBlend 状态")
    print("=" * 60)
    
    session = get_latest_session()
    if not session:
        print("❌ 未找到 CodeBlend session")
        return
    
    print(f"\n📁 Session: {session.name}")
    
    state = load_document_state(session)
    if state:
        print(f"   跟踪文件数: {len(state)}")
        for file_path, lines in state.items():
            total = len(lines)
            ai = sum(1 for l in lines if l == 2)
            human = sum(1 for l in lines if l == 1)
            if ai + human > 0:
                ai_pct = ai / (ai + human) * 100
                print(f"   - {os.path.basename(file_path)}: AI={ai}, Human={human}, AI%={ai_pct:.1f}%")
    
    print(f"\n📝 最近的 Commits:")
    for repo_dir in REPO_DIR.glob("*/commits"):
        commits = sorted(repo_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        for cf in commits:
            try:
                with open(cf) as f:
                    d = json.load(f)
                total = d.get('totalChanged', 0)
                ai = d.get('ai', 0)
                ai_pct = (ai / total * 100) if total > 0 else 0
                commit_hash = d.get('commit', cf.stem)[:12]
                print(f"   - {commit_hash}: AI={ai}, Total={total}, AI%={ai_pct:.1f}%")
            except:
                pass


def cmd_inject(ai_ratio: float, files: List[str] = None):
    """注入 AI 状态到 document-state.json (pre-commit 使用)"""
    session = get_latest_session()
    if not session:
        print("❌ 未找到 CodeBlend session")
        return False
    
    state = load_document_state(session)
    if not state:
        print("❌ document-state.json 为空")
        return False
    
    if files:
        count = sum(1 for f in files if inject_file_state(state, f, ai_ratio))
    else:
        count = inject_all_state(state, ai_ratio)
    
    if count > 0:
        save_document_state(session, state)
        print(f"✅ 已注入 {count} 个文件，AI 比例: {ai_ratio*100:.0f}%")
        print("⚠️  注意: 需在 commit 前执行才能影响上传数据")
        return True
    else:
        print("⚠️ 没有需要注入的文件")
        return False


def cmd_patch(commit_hash: str, ai_ratio: float):
    """修改已提交的 commit JSON (post-commit，仅影响本地显示)"""
    commit_files = list(REPO_DIR.glob(f"*/commits/{commit_hash}*.json"))
    if not commit_files:
        print(f"❌ 找不到 commit: {commit_hash}")
        return False
    
    commit_file = commit_files[0]
    if patch_commit_json(commit_file, ai_ratio):
        print(f"✅ 已修改 commit: {commit_hash[:12]}")
        print("⚠️  注意: 仅影响本地显示，不影响已上传的远程数据")
        return True
    return False


def cmd_precommit(repo_path: str, ai_ratio: float):
    """Pre-commit hook 模式 (推荐，可影响上传数据)"""
    session = get_latest_session()
    if not session:
        return 0
    
    state = load_document_state(session)
    if not state:
        return 0
    
    staged_files = get_staged_files(repo_path)
    if not staged_files:
        return 0
    
    count = 0
    for f in staged_files:
        if inject_file_state(state, f, ai_ratio):
            count += 1
    
    if count > 0:
        save_document_state(session, state)
        print(f"🔧 Pre-commit: 注入 {count} 个文件，AI={ai_ratio*100:.0f}%")
    
    return 0  # 不阻止 commit


def cmd_postcommit(repo_path: str, ai_ratio: float):
    """Post-commit hook 模式 (仅影响本地显示)"""
    import time
    time.sleep(1)  # 等待 CodeBlend 处理
    
    commit_hash = get_latest_commit_hash(repo_path)
    if not commit_hash:
        return 0
    
    # 查找 commit 文件
    for _ in range(5):
        commit_files = list(REPO_DIR.glob(f"*/commits/{commit_hash}.json"))
        if commit_files:
            break
        time.sleep(1)
    
    if commit_files and patch_commit_json(commit_files[0], ai_ratio):
        print(f"🔧 Post-commit: {commit_hash[:8]} AI={ai_ratio*100:.0f}%")
    
    return 0


def cmd_install_hook(repo_path: str, ai_ratio: float, hook_type: str = "pre"):
    """安装 Git hook"""
    git_dir = Path(repo_path) / '.git' / 'hooks'
    if not git_dir.exists():
        print("❌ 不在 Git 仓库中")
        return
    
    script_path = os.path.abspath(__file__)
    
    if hook_type == "pre":
        hook_path = git_dir / "pre-commit"
        mode = "precommit"
        desc = "Pre-Commit (推荐，可影响上传数据)"
    else:
        hook_path = git_dir / "post-commit"
        mode = "postcommit"
        desc = "Post-Commit (仅影响本地显示)"
    
    hook_content = f'''#!/bin/bash
# CodeBlend AI Injector - {desc}
python3 "{script_path}" {mode} --repo "{repo_path}" --ratio {ai_ratio}
'''
    
    with open(hook_path, 'w') as f:
        f.write(hook_content)
    os.chmod(hook_path, 0o755)
    
    print(f"✅ 已安装 {hook_type}-commit hook")
    print(f"   AI 比例: {ai_ratio*100:.0f}%")
    print(f"   位置: {hook_path}")


def cmd_uninstall_hook(repo_path: str):
    """卸载 Git hook"""
    git_dir = Path(repo_path) / '.git' / 'hooks'
    for hook_name in ['pre-commit', 'post-commit']:
        hook_path = git_dir / hook_name
        if hook_path.exists():
            with open(hook_path) as f:
                if 'CodeBlend AI Injector' in f.read():
                    os.remove(hook_path)
                    print(f"✅ 已卸载 {hook_name} hook")


# ==================== 主程序 ====================

def main():
    parser = argparse.ArgumentParser(
        description="🔧 CodeBlend AI Injector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s status                           # 查看状态
  %(prog)s inject --ratio 0.95              # 注入所有文件 (commit 前)
  %(prog)s patch abc123 --ratio 0.95        # 修改 commit (commit 后)
  %(prog)s install --repo . --type pre      # 安装 pre-commit hook (推荐)

⚠️ 重要说明:
  - pre-commit: 在 commit 前修改 document-state.json，可影响上传数据
  - post-commit: 在 commit 后修改 commit JSON，仅影响本地 UI 显示
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # status
    subparsers.add_parser('status', help='显示当前状态')
    
    # inject
    p = subparsers.add_parser('inject', help='注入 AI 状态 (commit 前使用)')
    p.add_argument('--ratio', '-r', type=float, default=DEFAULT_AI_RATIO)
    p.add_argument('--files', '-f', nargs='*', help='指定文件')
    
    # patch
    p = subparsers.add_parser('patch', help='修改 commit JSON (仅本地)')
    p.add_argument('commit', help='Commit hash')
    p.add_argument('--ratio', '-r', type=float, default=DEFAULT_AI_RATIO)
    
    # precommit
    p = subparsers.add_parser('precommit', help='Pre-commit hook 模式')
    p.add_argument('--repo', default='.', help='仓库路径')
    p.add_argument('--ratio', '-r', type=float, default=DEFAULT_AI_RATIO)
    
    # postcommit
    p = subparsers.add_parser('postcommit', help='Post-commit hook 模式')
    p.add_argument('--repo', default='.', help='仓库路径')
    p.add_argument('--ratio', '-r', type=float, default=DEFAULT_AI_RATIO)
    
    # install
    p = subparsers.add_parser('install', help='安装 Git hook')
    p.add_argument('--repo', default='.', help='仓库路径')
    p.add_argument('--ratio', '-r', type=float, default=DEFAULT_AI_RATIO)
    p.add_argument('--type', '-t', choices=['pre', 'post'], default='pre', 
                   help='hook 类型: pre(推荐) 或 post')
    
    # uninstall
    p = subparsers.add_parser('uninstall', help='卸载 Git hook')
    p.add_argument('--repo', default='.', help='仓库路径')
    
    args = parser.parse_args()
    
    if not args.command or args.command == 'status':
        cmd_status()
    elif args.command == 'inject':
        cmd_inject(args.ratio, args.files)
    elif args.command == 'patch':
        cmd_patch(args.commit, args.ratio)
    elif args.command == 'precommit':
        sys.exit(cmd_precommit(os.path.abspath(args.repo), args.ratio))
    elif args.command == 'postcommit':
        sys.exit(cmd_postcommit(os.path.abspath(args.repo), args.ratio))
    elif args.command == 'install':
        cmd_install_hook(os.path.abspath(args.repo), args.ratio, args.type)
    elif args.command == 'uninstall':
        cmd_uninstall_hook(os.path.abspath(args.repo))


if __name__ == '__main__':
    main()
