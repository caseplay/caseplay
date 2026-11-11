"""API persistence, session isolation, evidence gates and AI failure recovery."""
import copy
import json
import os
import sys
from pathlib import Path
import pytest
os.environ['CASEPLAY_FACTORY_ONLY'] = '1'
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'LMT_Server'))
import main
from storage import User
from catalog import validate_script
from utils.ai import AIError, normalize_scene

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///' + str(tmp_path / 'test.db'))
    monkeypatch.setattr(main, 'generate_scene', lambda *args, **kw: scene(kw.get('finish', False)))
    app = main.create_app(testing=True)
    with app.test_client() as client:
        yield client, app
    app.config['DB_ENGINE'].dispose()

def scene(ended=False):
    return {'narrator_text': '班主任请同学梳理已经看到的事实。', 'npc_dialogues': [{'name':'班主任','text':'先保存线索，再一起确认安全的求助方式。'}], 'choices': [] if ended else ['与班主任沟通','整理事实'], 'is_ended': ended, 'end_report': '本次行动尝试区分事实与推测，建议继续核实线索。' if ended else None, 'feedback': [{'dimension':'证据思维','observation':'呈递了已解锁线索。','suggestion':'补充时间信息。'}] if ended else [], 'model_label':'test-model'}

def signup(c, email='student@example.test'):
    r=c.post('/api/auth/register',json={'email':email,'display_name':'测试同学','password':'Testing123!','accepted_terms':True})
    assert r.status_code==201, r.json
    return {'Authorization':'Bearer '+r.json['token']}

def start(c,h):
    r=c.post('/api/play/start',headers=h,json={'script_id':'Script01.md','character':'被欺凌学生'})
    assert r.status_code==201,r.json
    return r.json['session_id']

def test_registration_auth_and_logout(client):
    c,app=client; h=signup(c)
    assert c.post('/api/auth/register',json={'email':'bad','password':'short'}).status_code==400
    assert c.post('/api/auth/register',json={'email':'student@example.test','display_name':'测试同学','password':'Testing123!','accepted_terms':True}).status_code==409
    assert c.get('/api/auth/me',headers={'Authorization':'Bearer 1'}).status_code==401
    assert c.post('/api/auth/login',json={'email':'student@example.test','password':'wrong'}).status_code==401
    assert c.post('/api/auth/login',json={'email':'student@example.test','password':'Testing123!'}).status_code==200
    with app.config['DB_FACTORY']() as db:
        assert db.get(User,1).password_hash!='Testing123!'
    assert c.post('/api/auth/logout',headers=h).status_code==200
    assert c.get('/api/auth/me',headers=h).status_code==401

def test_catalog_filter_favorites(client):
    c,_=client;h=signup(c)
    allcases=c.get('/api/scripts',headers=h).json
    assert len(allcases)==10
    for s in allcases:
        assert 'context' not in s and 'evidence' not in s
    assert all(s['category']=='校园保护' for s in c.get('/api/scripts?category=校园保护',headers=h).json)
    assert c.post('/api/scripts/Script01.md/favorite',headers=h).json['favorite']
    assert len(c.get('/api/scripts?favorite=1',headers=h).json)==1
    catalog=json.loads((Path(__file__).resolve().parents[1]/'LMT_Script/catalog.json').read_text())
    for s in catalog['scripts']: validate_script(copy.deepcopy(s))

def test_ownership_unlock_finish_and_persist(client):
    c,app=client;h=signup(c);sid=start(c,h);other=signup(c,'other@example.test')
    for path in [f'/api/sessions/{sid}',f'/api/report/{sid}',f'/api/sessions/{sid}/export']:
        assert c.get(path,headers=other).status_code==404
    assert c.post('/api/play/action',headers=other,json={'session_id':sid,'action':'查看'}).status_code==404
    initial=c.get(f'/api/sessions/{sid}',headers=h).json
    assert len(initial['evidence'])==2 and 'evidence' not in initial['script']
    assert initial['script']['evidence_count']==4
    assert c.post('/api/play/action',headers=h,json={'session_id':sid,'action':'查看','evidence_ids':['e4']}).status_code==400
    r=c.post('/api/play/action',headers=h,json={'session_id':sid,'action':'核对线索','evidence_ids':['e1'],'target':'班主任'})
    assert r.status_code==200 and len(r.json['session']['evidence'])==3
    assert c.get(f'/api/report/{sid}',headers=h).status_code==409
    assert c.post('/api/play/action',headers=h,json={'session_id':sid,'action':'结束并复盘','finish':True}).status_code==200
    report=c.get(f'/api/report/{sid}',headers=h).json
    assert report['metrics']['turns']==2 and report['metrics']['evidence_count']==1
    assert c.post(f'/api/sessions/{sid}/reflection',headers=h,json={'reflection':'下次先核实事实'}).status_code==200
    assert c.get(f'/api/sessions/{sid}/export',headers=h).json['reflection']=='下次先核实事实'
    assert c.get('/api/dashboard',headers=h).json['completed']==1
    assert c.get('/api/history',headers=h).json[0]['status']=='ended'
    assert c.post('/api/play/action',headers=h,json={'session_id':sid,'action':'再次操作'}).status_code==409

def test_ai_failure_does_not_charge_or_write(client,monkeypatch):
    c,_=client;h=signup(c)
    def fail(*a,**kw): raise AIError('测试接口暂不可用')
    monkeypatch.setattr(main,'generate_scene',fail)
    assert c.post('/api/play/start',headers=h,json={'script_id':'Script01.md','character':'被欺凌学生'}).status_code==502
    assert c.get('/api/auth/me',headers=h).json['remaining_plays']==100
    monkeypatch.setattr(main,'generate_scene',lambda *a,**kw:scene())
    sid=start(c,h)
    monkeypatch.setattr(main,'generate_scene',fail)
    assert c.post('/api/play/action',headers=h,json={'session_id':sid,'action':'核实情况'}).status_code==502
    data=c.get(f'/api/sessions/{sid}',headers=h).json
    assert data['metrics']['turns']==0 and len(data['chat_history'])==1
    monkeypatch.setattr(main,'generate_scene',lambda *a,**kw:scene())
    assert c.post('/api/play/action',headers=h,json={'session_id':sid,'action':'再次核实'}).status_code==200

def test_draft_review_permissions(client,monkeypatch):
    c,app=client;h=signup(c)
    assert c.get('/api/admin/users',headers=h).status_code==403
    with app.config['DB_FACTORY']() as db:
        db.get(User,1).is_admin=True;db.commit()
    seed=json.loads((Path(__file__).resolve().parents[1]/'LMT_Script/catalog.json').read_text())['scripts'][0]
    monkeypatch.setattr(main,'generate_script',lambda *a:copy.deepcopy(seed))
    draft=c.post('/api/admin/drafts/generate',headers=h,json={'topic':'校园保护教学案例','category':'校园保护'})
    assert draft.status_code==201,draft.json
    url='/api/admin/drafts/'+draft.json['id']
    assert len(c.get('/api/scripts',headers=h).json)==10
    assert c.post(url+'/publish',headers=h,json={'review_note':'通过'}).status_code==400
    assert c.post(url+'/publish',headers=h,json={'review_note':'已核查线索一致性与法规适用条件'}).status_code==200
    assert len(c.get('/api/scripts',headers=h).json)==11
    assert c.put(url,headers=h,json={'payload':seed}).status_code==409

def test_incomplete_model_output_is_rejected():
    with pytest.raises(AIError): normalize_scene({'narrator_text':'场景','is_ended':True},'test')
    with pytest.raises(AIError): normalize_scene(scene(),'test',finish=True)


def test_legacy_database_migrates_without_losing_history(tmp_path, monkeypatch):
    import sqlite3, hashlib
    path=tmp_path/'legacy.db'
    conn=sqlite3.connect(path)
    conn.executescript("CREATE TABLE users(id INTEGER PRIMARY KEY,email VARCHAR(255) UNIQUE NOT NULL,password_hash VARCHAR(255) NOT NULL,remaining_plays INTEGER,is_admin BOOLEAN,created_at DATETIME); CREATE TABLE sessions(id INTEGER PRIMARY KEY,user_id INTEGER,script_id VARCHAR(255),character_name VARCHAR(255),chat_history JSON,current_scene TEXT,created_at DATETIME);")
    conn.execute('INSERT INTO users VALUES(1,?,?,?,?,?)',('legacy@example.test',hashlib.sha256(b'LegacyPassword123!').hexdigest(),8,False,'2026-01-01 00:00:00'))
    conn.execute('INSERT INTO sessions VALUES(1,1,?,?,?,?,?)',('Script01.md','被欺凌学生',json.dumps([{'role':'ai','content':scene()}],ensure_ascii=False),'保留的旧场景','2026-01-01 00:00:00'))
    conn.commit();conn.close()
    monkeypatch.setenv('DATABASE_URL','sqlite:///'+str(path))
    app=main.create_app(testing=True)
    with app.test_client() as c:
        r=c.post('/api/auth/login',json={'email':'legacy@example.test','password':'LegacyPassword123!'})
        assert r.status_code==200
        h={'Authorization':'Bearer '+r.json['token']}
        assert c.get('/api/history',headers=h).json[0]['id']==1
        assert c.get('/api/sessions/1',headers=h).json['chat_history'][0]['content']['narrator_text']==scene()['narrator_text']
        assert c.get('/api/auth/me',headers=h).json['remaining_plays']==8
    with app.config['DB_FACTORY']() as db:
        assert db.get(User,1).password_hash.startswith('scrypt:')
    app.config['DB_ENGINE'].dispose()
