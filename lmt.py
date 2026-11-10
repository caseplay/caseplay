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
    parser.add_argument('command', choices=['init', 'serve', 'db-init', 'up', 'down'])
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
            from utils.db import get_db_connection
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    for statement in (ROOT / 'db_init.sql').read_text().split(';'):
                        if statement.strip():
                            cursor.execute(statement)
                connection.commit()
            finally:
                connection.close()

if __name__ == '__main__':
    main()
