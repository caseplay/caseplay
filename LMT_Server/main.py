"""Caseplay: authenticated, evidence-aware interactive legal education."""
import hashlib
import hmac
import json
import os
import re
import secrets
from collections import defaultdict
from datetime import timedelta
from functools import wraps
from pathlib import Path
from threading import Lock
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / '.env')
from flask import Flask, g, request, jsonify, Response
from flask_cors import CORS
from sqlalchemy import select, update, delete, func, or_
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from storage import make_storage, initialize, User, LoginToken, PlaySession, Favorite, ScriptDraft, now
from catalog import scripts, find_script, validate_script, legal_sources, CATEGORIES
from utils.ai import generate_scene, generate_script, AIError

EMAIL = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


def iso(value):
    return value.isoformat() + 'Z' if value else None


def create_app(testing=False):
    app = Flask(__name__)
    app.config.update(TESTING=testing, MAX_CONTENT_LENGTH=1024*1024)
    origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
    CORS(app, resources={r'/api/*': {'origins': origins}})
    engine, factory = make_storage()
    initialize(engine)
    app.config.update(DB_FACTORY=factory, DB_ENGINE=engine)
    login_attempts = defaultdict(list)
    rate_lock = Lock()

    @app.before_request
    def db_open():
        g.db = factory()

    @app.teardown_request
    def db_close(_):
        if 'db' in g:
            g.db.rollback()
            g.db.close()

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-store' if request.path.startswith('/api/auth') else 'private, no-cache'
        return response

    @app.errorhandler(ValueError)
    def invalid(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(AIError)
    def model_error(error):
        return jsonify(error=str(error), retryable=True), 502

    def auth(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            token = request.headers.get('Authorization', '').removeprefix('Bearer ').strip()
            if not token:
                return jsonify(error='请先登录'), 401
            hashed = hashlib.sha256(token.encode()).hexdigest()
            login = g.db.get(LoginToken, hashed)
            if not login or login.expires_at <= now():
                return jsonify(error='登录已失效，请重新登录'), 401
            user = g.db.get(User, login.user_id)
            if not user:
                return jsonify(error='账号不存在'), 401
            g.user, g.token = user, login
            return fn(*args, **kwargs)
        return wrapped

    def admin(fn):
        @auth
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not g.user.is_admin:
                return jsonify(error='需要内容管理员权限'), 403
            return fn(*args, **kwargs)
        return wrapped

    def body():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValueError('请求需要有效的 JSON 数据')
        return data

    def public_user(user):
        return {'id': user.id, 'email': user.email, 'display_name': user.display_name, 'is_admin': user.is_admin, 'remaining_plays': user.remaining_plays, 'created_at': iso(user.created_at)}

    def issue_token(user):
        raw = secrets.token_urlsafe(40)
        g.db.add(LoginToken(token_hash=hashlib.sha256(raw.encode()).hexdigest(), user_id=user.id, expires_at=now()+timedelta(days=7)))
        user.last_login = now()
        g.db.commit()
        return {'token': raw, 'user': public_user(user)}

    def owned_session(sid):
        session = g.db.get(PlaySession, sid)
        if session is None or session.user_id != g.user.id:
            return None
        return session

    def turns(session):
        return sum(1 for e in (session.events or []) if e.get('type') == 'action')

    def visible_evidence(script, turn):
        return [e for e in script.get('evidence', []) if e.get('unlock_turn', 0) <= turn]

    def metrics(session):
        events = session.events or []
        return {'turns': turns(session), 'evidence_count': len(set(session.evidence_used or [])), 'custom_actions': sum(1 for e in events if e.get('type') == 'action' and e.get('mode') == 'custom'), 'elapsed_seconds': max(0, int(((session.updated_at or now())-session.created_at).total_seconds())), 'reflection_saved': bool(session.reflection)}

    def serialize_session(session, detail=False):
        script = session.script_snapshot or find_script(g.db, session.script_id) or {'title': '已归档剧本', 'roles': [], 'evidence': [], 'legal_references': []}
        result = {'id': session.id, 'session_id': session.id, 'script_id': session.script_id, 'script_title': script['title'], 'character_name': session.character_name, 'status': session.status, 'created_at': iso(session.created_at), 'updated_at': iso(session.updated_at), 'metrics': metrics(session)}
        if detail:
            result.update(script={k: v for k, v in script.items() if k != 'evidence'} | {'evidence_count': len(script.get('evidence', []))}, chat_history=session.chat_history or [], evidence=visible_evidence(script, turns(session)), evidence_used=session.evidence_used or [], end_report=session.end_report, feedback=(session.report_data or {}).get('feedback', []), reflection=session.reflection or '', events=session.events or [], model_label=(session.report_data or {}).get('model_label') or os.getenv('AI_MODEL') or os.getenv('AI_PROVIDER', 'gemini').title())
        return result

    @app.get('/api/health')
    def health():
        return jsonify(status='ok', version='0.2.0', ai_provider=os.getenv('AI_PROVIDER', 'gemini'))

    @app.get('/api/auth/options')
    def auth_options():
        return jsonify(email_verification_required=False, registration_open=True)

    @app.post('/api/auth/register')
    def register():
        data = body()
        email = str(data.get('email', '')).strip().lower()
        password = str(data.get('password', ''))
        name = str(data.get('display_name', '')).strip()
        if not EMAIL.fullmatch(email) or len(email) > 255:
            raise ValueError('请输入有效的邮箱地址')
        if not 8 <= len(password) <= 128:
            raise ValueError('密码长度需要为8至128位')
        if not 2 <= len(name) <= 40:
            raise ValueError('昵称长度需要为2至40个字符')
        if not data.get('accepted_terms'):
            raise ValueError('请先阅读并同意使用说明')
        if g.db.scalar(select(User).where(User.email == email)):
            return jsonify(error='该邮箱已注册，请直接登录'), 409
        user = User(email=email, display_name=name, password_hash=generate_password_hash(password), remaining_plays=100, is_admin=False)
        g.db.add(user)
        try:
            g.db.commit()
        except IntegrityError:
            g.db.rollback()
            return jsonify(error='该邮箱已注册'), 409
        return jsonify(issue_token(user)), 201

    @app.post('/api/auth/login')
    def login():
        data = body()
        email = str(data.get('email', '')).strip().lower()
        password = str(data.get('password', ''))
        if len(password) > 128:
            raise ValueError('密码长度不正确')
        ip = request.remote_addr or 'unknown'
        key = (ip, email)
        with rate_lock:
            cutoff = now()-timedelta(minutes=10)
            if len(login_attempts) > 2000:
                login_attempts.clear()
            login_attempts[key] = [t for t in login_attempts[key] if t > cutoff]
            if len(login_attempts[key]) >= 12:
                return jsonify(error='尝试次数过多，请稍后重试'), 429
            login_attempts[key].append(now())
        user = g.db.scalar(select(User).where(User.email == email))
        valid = False
        if user:
            if len(user.password_hash) == 64:
                valid = hmac.compare_digest(user.password_hash, hashlib.sha256(password.encode()).hexdigest())
                if valid:
                    user.password_hash = generate_password_hash(password)
            else:
                valid = check_password_hash(user.password_hash, password)
        if not valid:
            return jsonify(error='邮箱或密码不正确'), 401
        with rate_lock:
            login_attempts.pop(key, None)
        return jsonify(issue_token(user))

    @app.post('/api/auth/logout')
    @auth
    def logout():
        g.db.delete(g.token)
        g.db.commit()
        return jsonify(message='已退出登录')

    @app.get('/api/auth/me')
    @auth
    def me():
        return jsonify(public_user(g.user))

    @app.get('/api/scripts')
    @auth
    def list_scripts():
        favorites = set(g.db.scalars(select(Favorite.script_id).where(Favorite.user_id == g.user.id)))
        q = request.args.get('q', '').strip().lower()
        items = []
        for script in scripts(g.db):
            if request.args.get('category') and script['category'] != request.args['category']:
                continue
            if request.args.get('difficulty') and script['difficulty'] != request.args['difficulty']:
                continue
            if request.args.get('favorite') == '1' and script['id'] not in favorites:
                continue
            if q and q not in json.dumps(script, ensure_ascii=False).lower():
                continue
            items.append({k: v for k, v in script.items() if k not in ['context', 'evidence'] } | {'favorite': script['id'] in favorites, 'evidence_count': len(script.get('evidence', []))})
        return jsonify(items)

    @app.get('/api/scripts/<script_id>')
    @auth
    def script_detail(script_id):
        script = find_script(g.db, script_id)
        if not script:
            return jsonify(error='剧本不存在'), 404
        # Full evidence content is revealed by the session, not by the lobby.
        return jsonify({k: v for k, v in script.items() if k != 'evidence'} | {'evidence_count': len(script.get('evidence', [])), 'favorite': g.db.get(Favorite, (g.user.id, script_id)) is not None})

    @app.post('/api/scripts/<script_id>/favorite')
    @auth
    def favorite(script_id):
        if not find_script(g.db, script_id):
            return jsonify(error='剧本不存在'), 404
        saved = g.db.get(Favorite, (g.user.id, script_id))
        if saved:
            g.db.delete(saved)
        else:
            g.db.add(Favorite(user_id=g.user.id, script_id=script_id))
        g.db.commit()
        return jsonify(favorite=saved is None)

    @app.get('/api/dashboard')
    @auth
    def dashboard():
        rows = list(g.db.scalars(select(PlaySession).where(PlaySession.user_id == g.user.id).order_by(PlaySession.created_at.desc())))
        return jsonify(user=public_user(g.user), completed=sum(r.status == 'ended' for r in rows), total_sessions=len(rows), evidence_count=sum(metrics(r)['evidence_count'] for r in rows), reflection_count=sum(bool(r.reflection) for r in rows), recent=[serialize_session(r) for r in rows[:4]])

    @app.get('/api/history')
    @auth
    def history():
        rows = g.db.scalars(select(PlaySession).where(PlaySession.user_id == g.user.id).order_by(PlaySession.created_at.desc()))
        return jsonify([serialize_session(r) for r in rows])

    @app.post('/api/play/start')
    @auth
    def start():
        data = body()
        script = find_script(g.db, str(data.get('script_id', '')))
        character = str(data.get('character', ''))
        if not script:
            return jsonify(error='剧本不存在'), 404
        if character not in [r['name'] for r in script['roles']]:
            raise ValueError('请选择剧本中的角色')
        if g.user.remaining_plays <= 0:
            return jsonify(error='可用演绎次数不足，请联系管理员'), 403
        scene = generate_scene(script, character)
        charged = g.db.execute(update(User).where(User.id == g.user.id, User.remaining_plays > 0).values(remaining_plays=User.remaining_plays-1))
        if charged.rowcount != 1:
            g.db.rollback()
            return jsonify(error='可用演绎次数不足'), 403
        session = PlaySession(user_id=g.user.id, script_id=script['id'], character_name=character, script_snapshot=script, chat_history=[{'role': 'ai', 'content': scene}], current_scene=scene['narrator_text'], status='ended' if scene['is_ended'] else 'ongoing', end_report=scene.get('end_report'), events=[{'type': 'start', 'at': iso(now())}], evidence_used=[], report_data={'feedback': scene.get('feedback', []), 'model_label': scene.get('model_label', '')})
        g.db.add(session)
        g.db.commit()
        return jsonify(session_id=session.id, scene=scene), 201

    @app.get('/api/sessions/<int:sid>')
    @app.get('/api/play/<int:sid>')
    @auth
    def get_session(sid):
        session = owned_session(sid)
        if not session:
            return jsonify(error='对局不存在'), 404
        return jsonify(serialize_session(session, True))

    @app.post('/api/play/action')
    @auth
    def action():
        data = body()
        try:
            sid = int(data.get('session_id', 0))
        except (TypeError, ValueError):
            raise ValueError('对局编号不正确')
        session = owned_session(sid)
        if not session:
            return jsonify(error='对局不存在'), 404
        if session.status != 'ongoing':
            return jsonify(error='本次演绎已结束'), 409
        action_text = str(data.get('action', '')).strip()
        if not action_text or len(action_text) > 1500:
            raise ValueError('请输入1至1500字的行动内容')
        script = session.script_snapshot or find_script(g.db, session.script_id)
        if not script:
            return jsonify(error='剧本已归档，暂无法继续'), 409
        evidence_ids = data.get('evidence_ids', [])
        available = {e['id'] for e in visible_evidence(script, turns(session))}
        if not isinstance(evidence_ids, list) or any(e not in available for e in evidence_ids):
            raise ValueError('只能呈递已解锁的线索')
        target = str(data.get('target', '')).strip()
        if target and target not in [r['name'] for r in script['roles']]:
            raise ValueError('对话对象不属于当前剧本')
        acquired = g.db.execute(update(PlaySession).where(PlaySession.id == sid, or_(PlaySession.is_busy == False, PlaySession.busy_at < now()-timedelta(seconds=180))).values(is_busy=True, busy_at=now()))
        if acquired.rowcount != 1:
            g.db.rollback()
            return jsonify(error='上一轮正在生成，请稍候'), 409
        g.db.commit()
        try:
            scene = generate_scene(script, session.character_name, action_text, session.chat_history or [], evidence_ids=evidence_ids, target=target, finish=bool(data.get('finish')))
            used = list(dict.fromkeys((session.evidence_used or []) + evidence_ids))
            event = {'type': 'action', 'at': iso(now()), 'text': action_text, 'mode': 'choice' if data.get('mode') == 'choice' else 'custom', 'evidence_ids': evidence_ids, 'target': target}
            session.chat_history = (session.chat_history or []) + [{'role': 'user', 'content': action_text, 'evidence_ids': evidence_ids, 'target': target}, {'role': 'ai', 'content': scene}]
            session.current_scene = scene['narrator_text']
            session.events = (session.events or []) + [event]
            session.evidence_used = used
            session.updated_at = now()
            if scene['is_ended']:
                session.status = 'ended'
                session.end_report = scene.get('end_report')
                session.report_data = {'feedback': scene.get('feedback', []), 'model_label': scene.get('model_label')}
            session.is_busy = False
            g.db.commit()
        except Exception:
            g.db.rollback()
            g.db.execute(update(PlaySession).where(PlaySession.id == sid).values(is_busy=False))
            g.db.commit()
            raise
        return jsonify(scene=scene, session=serialize_session(session, True))

    @app.get('/api/report/<int:sid>')
    @auth
    def report(sid):
        session = owned_session(sid)
        if not session:
            return jsonify(error='报告不存在'), 404
        if session.status != 'ended':
            return jsonify(error='请先完成本次推演'), 409
        return jsonify(serialize_session(session, True))

    @app.post('/api/sessions/<int:sid>/reflection')
    @auth
    def reflection(sid):
        session = owned_session(sid)
        if not session:
            return jsonify(error='对局不存在'), 404
        value = str(body().get('reflection', '')).strip()
        if len(value) > 4000:
            raise ValueError('复盘记录请控制在4000字以内')
        session.reflection = value
        g.db.commit()
        return jsonify(message='复盘已保存', reflection=value)

    @app.get('/api/sessions/<int:sid>/export')
    @auth
    def export(sid):
        session = owned_session(sid)
        if not session:
            return jsonify(error='对局不存在'), 404
        return Response(json.dumps(serialize_session(session, True), ensure_ascii=False, indent=2), mimetype='application/json', headers={'Content-Disposition': f'attachment; filename=caseplay-session-{sid}.json'})

    @app.get('/api/admin/users')
    @admin
    def admin_users():
        return jsonify([public_user(u) for u in g.db.scalars(select(User).order_by(User.id.desc()))])

    @app.put('/api/admin/users/<int:uid>')
    @admin
    def admin_user(uid):
        user = g.db.get(User, uid)
        if not user:
            return jsonify(error='用户不存在'), 404
        data = body()
        if 'remaining_plays' in data:
            user.remaining_plays = max(0, min(10000, int(data['remaining_plays'])))
        g.db.commit()
        return jsonify(public_user(user))

    def draft_data(d):
        return {'id': d.id, 'payload': d.payload, 'status': d.status, 'review_note': d.review_note, 'created_at': iso(d.created_at), 'reviewed_by': d.reviewed_by}

    @app.get('/api/admin/drafts')
    @admin
    def draft_list():
        return jsonify([draft_data(d) for d in g.db.scalars(select(ScriptDraft).order_by(ScriptDraft.created_at.desc()))])

    @app.post('/api/admin/drafts/generate')
    @admin
    def draft_generate():
        data = body()
        topic = str(data.get('topic', '')).strip()
        category = str(data.get('category', '校园保护'))
        if not 4 <= len(topic) <= 300 or category not in CATEGORIES:
            raise ValueError('请输入4至300字的剧本主题，并选择有效分类')
        payload = validate_script(generate_script(topic, category, legal_sources()))
        draft = ScriptDraft(id='draft-'+secrets.token_hex(8), payload=payload, created_by=g.user.id)
        g.db.add(draft)
        g.db.commit()
        return jsonify(draft_data(draft)), 201

    @app.put('/api/admin/drafts/<draft_id>')
    @admin
    def draft_edit(draft_id):
        draft = g.db.get(ScriptDraft, draft_id)
        if not draft:
            return jsonify(error='草稿不存在'), 404
        if draft.status == 'published':
            return jsonify(error='已发布版本不可直接覆盖，请创建新草稿'), 409
        draft.payload = validate_script(body().get('payload'))
        g.db.commit()
        return jsonify(draft_data(draft))

    @app.post('/api/admin/drafts/<draft_id>/publish')
    @admin
    def draft_publish(draft_id):
        draft = g.db.get(ScriptDraft, draft_id)
        if not draft:
            return jsonify(error='草稿不存在'), 404
        note = str(body().get('review_note', '')).strip()
        if not 8 <= len(note) <= 2000:
            raise ValueError('请填写至少8字的人工审校意见')
        draft.payload = validate_script(draft.payload)
        draft.status, draft.review_note, draft.reviewed_by = 'published', note, g.user.id
        g.db.commit()
        return jsonify(draft_data(draft))

    return app


app = create_app() if os.getenv('CASEPLAY_FACTORY_ONLY') != '1' else None
if __name__ == '__main__':
    app.run(host=os.getenv('HOST', '127.0.0.1'), port=int(os.getenv('PORT', '5000')), debug=False)
