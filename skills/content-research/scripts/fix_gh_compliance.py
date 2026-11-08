#!/usr/bin/env python3
"""
按 github-write-rules.md 规范修复 GitHub 项目记录
主要修复：英文描述、推荐理由含星数、项目类型
"""
import json
import re
import requests
import time
import os


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

def is_english(text):
    """检查文本是否主要是英文"""
    if not text or len(text) < 10:
        return False
    ascii_count = sum(1 for c in text[:80] if ord(c) < 128)
    return ascii_count / min(len(text[:80]), 80) > 0.7

def generate_chinese_desc(info, repo_name):
    """生成中文描述（符合日报格式）"""
    desc = info.get('description', '') or ''
    lang = info.get('language', '') or '未知语言'
    topics = info.get('topics', [])
    
    # 如果有中文描述，直接使用
    if desc and any('\u4e00' <= c <= '\u9fff' for c in desc):
        return desc
    
    # 如果有英文描述，生成中文版本
    if desc:
        return f"{desc}（{lang}）"
    
    # 根据 topics 生成
    if topics:
        topic_str = '、'.join(topics[:3])
        return f"{repo_name} - {topic_str}"
    
    return f"{repo_name} ({lang})"

def generate_reason(repo, info, track):
    """生成推荐理由（禁止包含星数）"""
    desc = info.get('description', '') or ''
    
    # 根据赛道生成不同的理由模板
    reason_templates = {
        '企业AI应用': '企业级 AI 工作流框架，适合生产环境部署',
        '内容创作': 'AI 内容创作工具，可提升创作效率',
        '效率提升': '开发效率工具，显著提升工作流效率',
        '工具': '实用工具库，解决特定场景需求',
        'skill': 'Agent 技能库，可扩展 AI 能力',
        '框架': 'AI 开发框架，提供完整解决方案',
    }
    
    # 匹配赛道
    matched_template = None
    track_lower = (track or '').lower()
    for key in reason_templates:
        if key.lower() in track_lower or key.lower() in str(info.get('topics', [])).lower():
            matched_template = reason_templates[key]
            break
    
    if matched_template:
        return matched_template
    
    # 根据描述生成
    if desc:
        desc_short = desc[:40] + '...' if len(desc) > 40 else desc
        return f"{desc_short}，{track or '通用'}类项目"
    
    return f"GitHub 热门项目，{info.get('language', '多语言')}，功能丰富"

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
    if any(kw in all_text for kw in ['cli', 'tool', 'utility', 'editor', 'IDE', 'debugger',
                                       'linter', 'formatter', 'terminal', 'console']):
        return '工具'
    if any(kw in all_text for kw in ['content', 'blog', 'cms', 'wiki', 'knowledge',
                                       'documentation', 'newsletter', 'rss']):
        return '内容源'
    if any(kw in all_text for kw in ['platform', 'saas', 'cloud', 'hosting', 'service',
                                       'api', 'server', 'backend']):
        return '平台'
    if any(kw in all_text for kw in ['book', 'tutorial', 'course', 'learning', 'education',
                                       'awesome', 'list', 'collection']):
        return '书籍'
    if any(kw in all_text for kw in ['dataset', 'data', 'benchmark', 'corpus']):
        return '数据集'
    return '其他'

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

def main():
    env = load_env()
    gh_token = env.get('GH_TOKEN', '')
    
    # Get token
    r = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
        json={'app_id': env.get('FEISHU_APP_ID', ''), 'app_secret': env.get('FEISHU_APP_SECRET', '')}, timeout=10)
    token = r.json()['tenant_access_token']
    H = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
    
    # Get all records
    all_repos = {}
    page_token = None
    while True:
        params = {'page_size': 200}
        if page_token: params['page_token'] = page_token
        r = requests.get(f'{BASE}/records', headers=H, params=params, timeout=15)
        data = r.json()
        for rec in data.get('data', {}).get('items', []):
            name = rec.get('fields', {}).get('项目名称', '')
            if name: all_repos[name.lower()] = {'record_id': rec.get('record_id'), 'fields': rec.get('fields', {})}
        if not data.get('data', {}).get('has_more'): break
        page_token = data.get('data', {}).get('page_token')
    
    print(f'总记录数: {len(all_repos)}')
    
    # Find records to fix
    to_fix = []
    for name, data in all_repos.items():
        fields = data['fields']
        record_id = data['record_id']
        
        issues = []
        
        # Rule 2: 推荐理由禁止包含星数
        reason = fields.get('推荐理由', '')
        if reason and ('⭐' in reason or re.search(r'\d+k', reason, re.IGNORECASE)):
            issues.append('理由含星数')
        
        # Rule 3: 项目描述应该用中文
        desc = fields.get('项目描述', '')
        if desc and is_english(desc):
            issues.append('描述英文')
        
        # Rule 7: 项目类型应该从 API 动态解析
        project_type = fields.get('项目类型', '')
        if not project_type or project_type == '书籍':
            issues.append('类型待确认')
        
        if issues:
            to_fix.append((name, record_id, fields, issues))
    
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
        
        # Rule 2: Fix reason (remove star count)
        old_reason = fields.get('推荐理由', '')
        if old_reason and ('⭐' in old_reason or re.search(r'\d+k', old_reason, re.IGNORECASE)):
            update_fields['推荐理由'] = generate_reason(name, info, fields.get('推荐赛道', ''))
        
        # Rule 3: Fix English description
        old_desc = fields.get('项目描述', '')
        if old_desc and is_english(old_desc):
            update_fields['项目描述'] = generate_chinese_desc(info, name)
        
        # Rule 7: Fix project type
        old_type = fields.get('项目类型', '')
        new_type = detect_project_type(info)
        if old_type != new_type:
            update_fields['项目类型'] = new_type
        
        if update_fields:
            try:
                r = requests.put(f'{BASE}/records/{record_id}',
                    headers=H, json={'fields': update_fields}, timeout=15)
                if r.json().get('code') == 0:
                    print('✅')
                    success += 1
                else:
                    print(f'❌ {r.json().get("msg")}')
            except Exception as e:
                print(f'❌ {e}')
        else:
            print('⏭️ skip')
        
        time.sleep(0.15)
    
    print(f'\n完成: 成功 {success}/{len(to_fix)}')

if __name__ == '__main__':
    main()