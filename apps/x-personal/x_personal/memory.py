"""Local conversation history and facts explicitly saved by Ibrahim."""
from contextlib import contextmanager
import datetime as dt
from pathlib import Path
import re
import sqlite3

DATABASE = Path('D:/X-System/data/mind/memory.sqlite')

@contextmanager
def connect(path=None):
    target = Path(path or DATABASE)
    target.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(target), timeout=10)
    db.row_factory = sqlite3.Row
    try:
        db.executescript('''CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY, session TEXT NOT NULL, role TEXT NOT NULL,
            content TEXT NOT NULL, at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY, content TEXT NOT NULL UNIQUE, at TEXT NOT NULL);''')
        yield db
        db.commit()
    finally:
        db.close()

def validate_session(session):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', session):
        raise ValueError('Invalid conversation session')

def history(session, path=None):
    validate_session(session)
    with connect(path) as db:
        rows = db.execute('SELECT role,content FROM turns WHERE session=? ORDER BY id DESC LIMIT 8',(session,)).fetchall()
    return [dict(row) for row in reversed(rows)]

def append_pair(session, user, reply, path=None):
    validate_session(session)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    with connect(path) as db:
        db.executemany('INSERT INTO turns(session,role,content,at) VALUES (?,?,?,?)',
                       [(session,'user',user,now),(session,'assistant',reply,now)])

def remember(content, path=None):
    value = content.strip()
    if not value or len(value) > 1000:
        raise ValueError('اكتب معلومة من 1 إلى 1000 حرف')
    with connect(path) as db:
        db.execute('INSERT OR IGNORE INTO facts(content,at) VALUES (?,?)', (value,dt.datetime.now(dt.timezone.utc).isoformat()))

def facts(path=None):
    with connect(path) as db:
        return [dict(row) for row in db.execute('SELECT id,content FROM facts ORDER BY id DESC LIMIT 20')]

def forget(number, path=None):
    with connect(path) as db:
        return db.execute('DELETE FROM facts WHERE id=?',(int(number),)).rowcount > 0
