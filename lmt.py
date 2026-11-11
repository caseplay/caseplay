#!/usr/bin/env python3
"""Caseplay command line."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description='Caseplay部署工具')
    parser.add_argument('command', choices=['init', 'serve', 'db-init', 'up', 'down', 'admin'])
    parser.add_argument('email', nargs='?')
    args = parser.parse_args()
    os.chdir(ROOT)
    if args.command == 'init':
        target = ROOT / '.env'
        if not target.exists():
            target.write_text((ROOT / '.env.example').read_text())
            target.chmod(0o600)
        print('请编辑 .env 配置数据库、邮件及模型 API Key。')
    elif args.command in ('up', 'down'):
        subprocess.run(['docker', 'compose', *(['up', '-d', '--build'] if args.command == 'up' else ['down'])], check=True)
    else:
        from dotenv import load_dotenv
        load_dotenv(ROOT / '.env')
        sys.path.insert(0, str(ROOT / 'LMT_Server'))
        if args.command == 'serve':
            from main import app
            app.run(host=os.getenv('HOST', '127.0.0.1'), port=int(os.getenv('PORT', '5000')), debug=False)
        else:
            from storage import make_storage, initialize, User
            from sqlalchemy import select
            engine, factory = make_storage()
            initialize(engine)
            if args.command == 'admin':
                if not args.email:
                    parser.error('admin 需要已注册用户的邮箱')
                with factory() as db:
                    user = db.scalar(select(User).where(User.email == args.email.strip().lower()))
                    if user is None:
                        parser.error('该邮箱尚未注册')
                    user.is_admin = True
                    db.commit()
                print('已授予内容管理员权限。')
            else:
                print('数据库结构已初始化并完成兼容迁移。')

if __name__ == '__main__':
    main()
