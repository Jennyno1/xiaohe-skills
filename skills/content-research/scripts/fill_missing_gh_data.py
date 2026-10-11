#!/usr/bin/env python3
"""
使用 GitHub API 批量补齐缺少描述/理由的 GitHub 项目
"""
import json
import re
import requests
import time
import os
import sys
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))

import json
import os
import re
import time
from pathlib import Path

ENV_FILE = Path(os.environ.get("HERMES_ENV_FILE") or (Path.home() / ".hermes" / ".env"))
BINDINGS_FILE = Path(os.environ.get("CONTENT_RESEARCH_BINDINGS") or (Path.home() / ".hermes" / "bindings.yaml"))


def _bindings():
    """绑定配置：环境变量优先，其次 bindings.yaml（公开版不含真实值）"""
    cfg = {}
    if BINDINGS_FILE.is_file():
        try:
            import yaml
            cfg = yaml.safe_load(BINDINGS_FILE.read_text(encoding="utf-8")) or {}
        except Exception:
            cfg = {}
    tables = cfg.get("tables") or {}
    app_token = os.environ.get("FEISHU_BITABLE_APP_TOKEN") or tables.get("bitable_app_token")
    table_id = os.environ.get("FEISHU_GITHUB_TABLE_ID") or tables.get("github")
    if not app_token or not table_id:
        raise SystemExit(
            "缺少绑定配置：请设置 FEISHU_BITABLE_APP_TOKEN / FEISHU_GITHUB_TABLE_ID，"
            f"或在 {BINDINGS_FILE} 配置 tables.bitable_app_token / tables.github"
        )
    return app_token, table_id


_APP_TOKEN, _TABLE_ID = _bindings()
BASE = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{_APP_TOKEN}/tables/{_TABLE_ID}"

def load_env():
    env = {}
    for line in open(ENV_FILE):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'").strip()
    return env

def get_token(env):
    r = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
        json={'app_id': env.get('FEISHU_APP_ID', ''), 'app_secret': env.get('FEISHU_APP_SECRET', '')}, timeout=10)
    return r.json()['tenant_access_token']

def get_all_records(token):
    H = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
    repos = {}
    page_token = None
    while True:
        params = {'page_size': 200}
        if page_token:
            params['page_token'] = page_token
        r = requests.get(f'{BASE}/records', headers=H, params=params, timeout=15)
        data = r.json().get('data', {})
        for rec in data.get('items', []):
            name = rec.get('fields', {}).get('项目名称', '')
            if name:
                repos[name.lower()] = rec.get('fields', {})
        if not data.get('has_more'):
            break
        page_token = data.get('page_token')
    return repos

def fetch_github_info(repo, gh_token):
    """从 GitHub API 拉取仓库信息"""
    url = f'https://api.github.com/repos/{repo}'
    headers = {'Accept': 'application/vnd.github+json'}
    if gh_token:
        headers['Authorization'] = f'Bearer {gh_token}'
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            d = r.json()
            return {
                'stars': d.get('stargazers_count', 0),
                'forks': d.get('forks_count', 0),
                'language': d.get('language') or '',
                'description': d.get('description') or '',
                'created': (d.get('created_at') or '')[:10],
                'pushed': (d.get('pushed_at') or '')[:10],
                'topics': d.get('topics', []),
            }
        elif r.status_code == 403:
            time.sleep(5)
            return fetch_github_info(repo, gh_token)
    except:
        pass
    return None

def detect_project_type(gh_info):
    """根据 GitHub API 返回动态判断项目类型"""
    topics = [t.lower() for t in gh_info.get('topics', [])]
    lang = (gh_info.get('language') or '').lower()
    desc = (gh_info.get('description') or '').lower()
    all_text = ' '.join(topics) + ' ' + lang + ' ' + desc
    
    # 优先级：skill > 框架 > 工具 > 内容源 > 平台 > 书籍 > 数据集 > 其他
    if any(kw in all_text for kw in ['skill', 'claude-code', 'agent-skill', 'cursor-rule']):
        return 'skill'
    if any(kw in all_text for kw in ['framework', 'sdk', 'library', 'runtime', 'engine']):
        return '框架'
    if any(kw in all_text for kw in ['cli', 'tool', 'utility', 'editor', 'IDE', 'debugger']):
        return '工具'
    if any(kw in all_text for kw in ['content', 'blog', 'cms', 'wiki', 'knowledge']):
        return '内容源'
    if any(kw in all_text for kw in ['platform', 'saas', 'cloud', 'hosting', 'service']):
        return '平台'
    if any(kw in all_text for kw in ['book', 'tutorial', 'course', 'learning', 'awesome']):
        return '书籍'
    if any(kw in all_text for kw in ['dataset', 'data', 'benchmark', 'corpus']):
        return '数据集'
    return '其他'

def update_record(token, record_id, fields_update):
    """更新飞书记录"""
    H = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
    url = f'{BASE}/records/{record_id}'
    try:
        r = requests.put(url, headers=H, json={'fields': fields_update}, timeout=15)
        return r.json().get('code') == 0
    except Exception as e:
        print(f'⚠️ Update failed: {e}', file=sys.stderr)
        return False

def main():
    env = load_env()
    token = get_token(env)
    gh_token = env.get('GH_TOKEN', '')
    
    # Get current records
    all_repos = get_all_records(token)
    print(f'总记录数: {len(all_repos)}')
    
    # Find records with missing data
    to_fix = []
    for name, fields in all_repos.items():
        issues = []
        
        # Check description
        desc = fields.get('项目描述', '')
        if not desc or len(desc.strip()) < 5:
            issues.append('缺描述')
        
        # Check reason
        reason = fields.get('推荐理由', '')
        if not reason or len(reason.strip()) < 5:
            issues.append('缺理由')
        
        # Check type
        project_type = fields.get('项目类型', '')
        if not project_type or project_type == '书籍':  # '书籍' might be wrong
            issues.append('类型待确认')
        
        if issues:
            to_fix.append((name, fields.get('record_id', ''), fields, issues))
    
    print(f'需要修复: {len(to_fix)} 条')
    print()
    
    # Fix each record
    success = 0
    for i, (name, record_id, fields, issues) in enumerate(to_fix):
        print(f'[{i+1}/{len(to_fix)}] {name} ({", ".join(issues)})...', end=' ', flush=True)
        
        # Fetch GitHub info
        info = fetch_github_info(name, gh_token)
        if not info:
            print('❌ GitHub API 失败')
            continue
        
        # Prepare update fields
        update_fields = {}
        
        # Fix description
        old_desc = fields.get('项目描述', '')
        if not old_desc or len(old_desc.strip()) < 5:
            if info.get('description'):
                desc = info['description']
                # Use Chinese if available
                if any('\u4e00' <= c <= '\u9fff' for c in desc):
                    update_fields['项目描述'] = desc
                else:
                    update_fields['项目描述'] = f"{desc}（{info.get('language', '未知语言')}）"
        
        # Fix reason
        old_reason = fields.get('推荐理由', '')
        if not old_reason or len(old_reason.strip()) < 5:
            track = fields.get('推荐赛道', '')
            desc = info.get('description', '') or ''
            lang = info.get('language', '') or ''
            
            if desc:
                desc_short = desc[:40] + '...' if len(desc) > 40 else desc
                update_fields['推荐理由'] = f"{desc_short}，{track or '通用'}类项目"
            else:
                update_fields['推荐理由'] = f"GitHub 热门项目，{lang or '多语言'}，功能丰富"
        
        # Fix type
        old_type = fields.get('项目类型', '')
        new_type = detect_project_type(info)
        if old_type != new_type:
            update_fields['项目类型'] = new_type
        
        if update_fields:
            if update_record(token, record_id, update_fields):
                print('✅')
                success += 1
            else:
                print('❌')
        else:
            print('⏭️ skip')
        
        time.sleep(0.2)
    
    print(f'\n完成: 成功 {success}/{len(to_fix)}')

if __name__ == '__main__':
    main()