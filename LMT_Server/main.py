import os
import random
import hashlib
from flask import Flask, request, jsonify
from flask_cors import CORS

from utils.db import get_db_connection
from utils.mail import send_verification_code
from utils.ai import generate_scene

app = Flask(__name__)
CORS(app)

VERIFICATION_CODES = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/api/auth/send_code', methods=['POST'])
def send_code():
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400

    conn = get_db_connection()
    user_exists = False
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
            user_exists = bool(cursor.fetchone())
    finally:
        conn.close()

    code = f"{random.randint(100000, 999999)}"
    VERIFICATION_CODES[email] = code
    send_verification_code(email, code)
    return jsonify({"message": "Verification code sent", "user_exists": user_exists}), 200

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    code = data.get('code')
    password = data.get('password')

    if not all([email, code, password]):
        return jsonify({"error": "Missing fields"}), 400

    if VERIFICATION_CODES.get(email) != code:
        return jsonify({"error": "Invalid or expired verification code"}), 400

    del VERIFICATION_CODES[email]

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cursor.fetchone():
                hashed = hash_password(password)
                cursor.execute("UPDATE users SET password_hash=%s WHERE email=%s", (hashed, email))
                conn.commit()
                return jsonify({"message": "Password updated successfully", "is_update": True}), 200

            hashed = hash_password(password)
            cursor.execute("INSERT INTO users (email, password_hash, remaining_plays, is_admin) VALUES (%s, %s, 1, FALSE)", (email, hashed))
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            hashed = hash_password(password)
            cursor.execute("SELECT id, email FROM users WHERE email=%s AND password_hash=%s", (email, hashed))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "Invalid credentials"}), 401

            token = str(user['id'])
            return jsonify({"token": token, "email": user['email']}), 200
    finally:
        conn.close()

@app.route('/api/auth/me', methods=['GET'])
def get_user_info():
    token = request.args.get('token')
    if not token:
        return jsonify({"error": "Token is required"}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT email, remaining_plays, is_admin FROM users WHERE id=%s", (token,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "User not found"}), 404
            return jsonify({
                "email": user["email"],
                "remaining_plays": user["remaining_plays"],
                "is_admin": bool(user["is_admin"])
            }), 200
    finally:
        conn.close()

@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    token = request.args.get('token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT is_admin FROM users WHERE id=%s", (token,))
            admin_check = cursor.fetchone()
            if not admin_check or not admin_check['is_admin']:
                return jsonify({"error": "Forbidden"}), 403

            cursor.execute("SELECT id, email, remaining_plays, is_admin, created_at FROM users")
            users = cursor.fetchall()
            return jsonify(users), 200
    finally:
        conn.close()

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
def admin_update_user(user_id):
    token = request.json.get('token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT is_admin FROM users WHERE id=%s", (token,))
            admin_check = cursor.fetchone()
            if not admin_check or not admin_check['is_admin']:
                return jsonify({"error": "Forbidden"}), 403

            plays = request.json.get('remaining_plays')
            new_password = request.json.get('password')

            if plays is not None:
                cursor.execute("UPDATE users SET remaining_plays=%s WHERE id=%s", (plays, user_id))
            if new_password:
                hashed = hash_password(new_password)
                cursor.execute("UPDATE users SET password_hash=%s WHERE id=%s", (hashed, user_id))
        conn.commit()
        return jsonify({"message": "User updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

def parse_markdown_files():
    scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'LMT_Script')
    scripts = []
    if not os.path.exists(scripts_dir):
        return scripts

    for filename in os.listdir(scripts_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(scripts_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.split('\n')
            title = filename.replace('.md', '')
            roles = []
            for line in lines:
                if line.startswith('# '):
                    title = line[2:].strip()
                elif line.startswith('- '):
                    roles.append(line[2:].strip())
            scripts.append({"id": filename, "title": title, "roles": roles, "content": content})
    return scripts

@app.route('/api/scripts', methods=['GET'])
def get_scripts():
    scripts = parse_markdown_files()
    summaries = [{"id": s["id"], "title": s["title"]} for s in scripts]
    return jsonify(summaries), 200

@app.route('/api/scripts/<script_id>', methods=['GET'])
def get_script(script_id):
    scripts = parse_markdown_files()
    for s in scripts:
        if s["id"] == script_id:
            return jsonify(s), 200
    return jsonify({"error": "Script not found"}), 404

@app.route('/api/play/start', methods=['POST'])
def play_start():
    data = request.json
    user_id = data.get('token')
    script_id = data.get('script_id')
    character = data.get('character')

    if not all([user_id, script_id, character]):
        return jsonify({"error": "Missing fields"}), 400

    scripts = parse_markdown_files()
    script = next((s for s in scripts if s["id"] == script_id), None)
    if not script:
        return jsonify({"error": "Script not found"}), 404

    scene_data = generate_scene(script['content'], character)

    conn = get_db_connection()
    try:
        import json
        with conn.cursor() as cursor:
            # Check remaining plays
            cursor.execute("SELECT remaining_plays FROM users WHERE id=%s", (user_id,))
            user = cursor.fetchone()
            if not user or user['remaining_plays'] <= 0:
                return jsonify({"error": "No remaining plays available. You only have 1 play. Contact admin for more."}), 403

            # Decrement plays
            cursor.execute("UPDATE users SET remaining_plays = remaining_plays - 1 WHERE id=%s", (user_id,))

            history = [{"role": "ai", "content": scene_data}]
            cursor.execute(
                "INSERT INTO sessions (user_id, script_id, character_name, chat_history, current_scene, status) VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, script_id, character, json.dumps(history), scene_data.get('narrator_text', ''), 'ongoing')
            )
            session_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()

    return jsonify({"session_id": session_id, "scene": scene_data}), 200

@app.route('/api/play/action', methods=['POST'])
def play_action():
    data = request.json
    session_id = data.get('session_id')
    user_action = data.get('action')

    conn = get_db_connection()
    try:
        import json
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM sessions WHERE id=%s", (session_id,))
            session = cursor.fetchone()
            if not session:
                return jsonify({"error": "Session not found"}), 404

            if session.get('status') == 'ended':
                return jsonify({"error": "Session is already ended"}), 400

            scripts = parse_markdown_files()
            script = next((s for s in scripts if s["id"] == session['script_id']), None)
            script_content = script['content'] if script else "Unknown Context"

            history = json.loads(session['chat_history']) if session['chat_history'] else []
            history.append({"role": "user", "content": user_action})

            # Format history for AI
            formatted_history = []
            for item in history:
                if item['role'] == 'user':
                    formatted_history.append(f"USER ({session['character_name']}): {item['content']}")
                else:
                    c = item['content']
                    ai_text = f"NARRATOR: {c.get('narrator_text', '')}"
                    for dmg in c.get('npc_dialogues', []):
                        ai_text += f"\nNPC {dmg.get('name', 'Unknown')}: {dmg.get('text', '')}"
                    formatted_history.append(ai_text)

            history_str = "\n".join(formatted_history)

            scene_data = generate_scene(f"Script: {script_content} \n\nPast interactions:\n{history_str}", session['character_name'], user_action)
            history.append({"role": "ai", "content": scene_data})

            is_ended = scene_data.get('is_ended', False)
            status = 'ended' if is_ended else 'ongoing'
            end_report = scene_data.get('end_report', None)

            cursor.execute("UPDATE sessions SET chat_history=%s, current_scene=%s, status=%s, end_report=%s WHERE id=%s",
                           (json.dumps(history), scene_data.get('narrator_text', ''), status, end_report, session_id))
        conn.commit()
    finally:
        conn.close()

    return jsonify({"scene": scene_data, "status": status, "end_report": end_report}), 200

@app.route('/api/report/<session_id>', methods=['GET'])
def get_report(session_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, script_id, character_name, end_report, created_at FROM sessions WHERE id=%s AND status='ended'", (session_id,))
            session = cursor.fetchone()
            if not session:
                return jsonify({"error": "Report not found or session not ended"}), 404

            scripts = parse_markdown_files()
            script = next((s for s in scripts if s["id"] == session['script_id']), None)
            session['script_title'] = script['title'] if script else "Unknown Script"

            return jsonify(session), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/history', methods=['GET'])
def get_history():
    user_id = request.args.get('token')
    if not user_id:
        return jsonify({"error": "Token is required"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, script_id, character_name, status, end_report, created_at FROM sessions WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
            sessions = cursor.fetchall()

            scripts = parse_markdown_files()
            script_map = {s['id']: s['title'] for s in scripts}

            for s in sessions:
                s['script_title'] = script_map.get(s['script_id'], "Unknown Script")

            return jsonify(sessions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
