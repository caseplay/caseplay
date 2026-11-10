import os
import yaml
import pymysql

# Get absolute path to config.yaml
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.yaml')

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        result = yaml.safe_load(f) or {}
    for section, fields in {'mysql': {'host': 'MYSQL_HOST', 'port': 'MYSQL_PORT', 'user': 'MYSQL_USER', 'password': 'MYSQL_PASSWORD', 'database': 'MYSQL_DATABASE'}, 'QQ_Mail': {'SENDER': 'MAIL_SENDER', 'API_KEY': 'MAIL_API_KEY'}}.items():
        for field, env in fields.items():
            if env in os.environ:
                result.setdefault(section, {})[field] = int(os.environ[env]) if field == 'port' else os.environ[env]
    return result

config = load_config()

def get_db_connection():
    db_config = config['mysql']
    return pymysql.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        port=db_config['port'],
        cursorclass=pymysql.cursors.DictCursor
    )
