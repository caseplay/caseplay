"""Structured, educational fictional cases and human-reviewed AI drafts."""
import json
import os
from pathlib import Path
from sqlalchemy import select
from storage import ScriptDraft

CATALOG = Path(os.getenv('CASEPLAY_CATALOG', Path(__file__).resolve().parents[1] / 'LMT_Script' / 'catalog.json'))
CATEGORIES = ['校园保护', '网络安全', '民事生活', '科技社会']


def validate_script(data):
    if not isinstance(data, dict):
        raise ValueError('剧本数据必须是对象')
    for key in ['title', 'summary', 'context']:
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError('剧本缺少标题、简介或案件背景')
    if len(data['title']) > 80 or len(data['context']) > 20000:
        raise ValueError('剧本标题或背景过长')
    if data.get('category') not in CATEGORIES:
        raise ValueError('请选择有效主题')
    if data.get('difficulty') not in ['入门', '进阶', '挑战']:
        raise ValueError('请选择有效难度')
    if not isinstance(data.get('roles'), list) or not 2 <= len(data['roles']) <= 8:
        raise ValueError('剧本需要2至8个角色')
    for role in data['roles']:
        if not isinstance(role, dict) or not isinstance(role.get('name'), str) or not role['name'].strip():
            raise ValueError('角色需要有效名称')
        role.setdefault('description', '')
    if len({r['name'] for r in data['roles']}) != len(data['roles']):
        raise ValueError('角色名称不能重复')
    if not isinstance(data.get('goals'), list) or not data['goals'] or any(not isinstance(x, str) for x in data['goals']):
        raise ValueError('需要明确的学习目标')
    evidence = data.setdefault('evidence', [])
    if not isinstance(evidence, list) or len(evidence) > 12:
        raise ValueError('线索列表格式不正确')
    for i, item in enumerate(evidence):
        if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k].strip() for k in ['id', 'title', 'content']):
            raise ValueError('线索需要编号、标题和内容')
        item['unlock_turn'] = max(0, min(8, int(item.get('unlock_turn', i // 2))))
    if len({e['id'] for e in evidence}) != len(evidence):
        raise ValueError('线索编号不能重复')
    data.setdefault('legal_references', [])
    # Never publish model-invented external URLs; references are selected from the curated source list.
    data['legal_references'] = [r for r in data['legal_references'] if isinstance(r, dict) and r in legal_sources()]
    data['duration'] = max(5, min(60, int(data.get('duration', 15))))
    data.setdefault('accent', 'teal')
    data.setdefault('learning_points', data['goals'])
    return data


def legal_sources():
    return json.loads(CATALOG.read_text(encoding='utf-8'))['legal_sources']


def scripts(db):
    items = json.loads(CATALOG.read_text(encoding='utf-8'))['scripts']
    for draft in db.scalars(select(ScriptDraft).where(ScriptDraft.status == 'published')):
        items.append({**draft.payload, 'id': draft.id, 'reviewed': True})
    return items


def find_script(db, script_id):
    return next((s for s in scripts(db) if s['id'] == script_id), None)
