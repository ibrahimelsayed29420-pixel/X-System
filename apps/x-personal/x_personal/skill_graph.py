"""Local skill dependencies and observed experience, never executable model output."""
import datetime as dt
import hashlib
from pathlib import Path
import sqlite3
from contextlib import contextmanager

DATABASE=Path('D:/X-System/data/mind/skills.sqlite')
SKILLS={
 'dialogue':('المحادثة والشخصية','مصري كلام رد فهم سؤال English Arabic language bilingual'),
 'memory':('الذاكرة المحلية','احفظ افتكر ذاكرة اتعلم تصحيح remember memory learn'),
 'research':('البحث العام','بحث ابحث دور سوق مصادر research search sources'),
 'real_estate':('مساعد العقارات','عقار عقارات إيجار تأجير بيع أرض أراضي أوف بلان listing property real estate'),
 'workflow':('تنسيق المهام','خطة مهمة مراحل تنفيذ مهارة مهارات ربط plan task skill workflow'),
 'source_review':('مراجعة المصادر','مصادر رابط دليل تحقق'),
 'ollama':('الاستدلال المحلي','عقل فهم رد'),
 'semantic_memory':('استرجاع Mem0 الدلالي','ذاكرة ذكريات تفضيل معنى'),
 'planning':('تخطيط Deep Agents','خطة اختيار أدوات تنفيذ مهارة'),
}
EDGES=[('dialogue','memory','uses'),('dialogue','ollama','uses'),
       ('research','source_review','supports'),('workflow','research','uses'),
       ('dialogue','research','can_use'),('memory','dialogue','informs'),
       ('real_estate','research','can_use'),('real_estate','workflow','uses'),
       ('real_estate','memory','can_use'),
       ('memory','semantic_memory','uses'),('planning','ollama','uses'),
       ('planning','research','can_use'),('planning','memory','can_use'),
       ('dialogue','planning','uses')]

@contextmanager
def connect(path=None):
    target=Path(path or DATABASE);target.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(str(target),timeout=10)
    db.executescript('''CREATE TABLE IF NOT EXISTS skills(id TEXT PRIMARY KEY,title TEXT,tags TEXT,kind TEXT);
    CREATE TABLE IF NOT EXISTS edges(source TEXT,target TEXT,relation TEXT,PRIMARY KEY(source,target,relation));
    CREATE TABLE IF NOT EXISTS experience(id TEXT PRIMARY KEY,skill TEXT,ok INTEGER,at TEXT,error TEXT);
    CREATE TABLE IF NOT EXISTS lessons(id TEXT PRIMARY KEY,content TEXT,at TEXT);''')
    for key,(title,tags) in SKILLS.items():
        db.execute('INSERT INTO skills VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,tags=excluded.tags',(key,title,tags,'capability'))
    db.executemany('INSERT OR IGNORE INTO edges VALUES (?,?,?)',EDGES)
    db.commit()
    try:
        yield db
        db.commit()
    finally:
        db.close()

def record(request_id,intent,ok,error='',path=None):
    skill={'search':'research','direct':'memory','chat':'dialogue'}.get(intent,intent)
    if skill not in SKILLS:
        skill='dialogue'
    with connect(path) as db:
        db.execute('INSERT OR IGNORE INTO experience VALUES (?,?,?,?,?)',
                   (request_id,skill,int(bool(ok)),dt.datetime.now(dt.timezone.utc).isoformat(),error[:300]))
        if ok and skill=='research':
            db.execute('INSERT OR IGNORE INTO skills VALUES (?,?,?,?)',
                       ('procedure:research-cited','خبرة تنفيذ: بحث مع مصادر موثقة','بحث مصادر','procedure'))
            db.executemany('INSERT OR IGNORE INTO edges VALUES (?,?,?)',[
                ('procedure:research-cited','research','uses'),
                ('procedure:research-cited','source_review','uses')])

def learn(content,path=None):
    content=content.strip()
    if not content or len(content)>1000:raise ValueError('اكتب خبرة من 1 إلى 1000 حرف')
    key='lesson:'+hashlib.sha256(content.encode('utf-8')).hexdigest()[:20]
    with connect(path) as db:
        db.execute('INSERT OR IGNORE INTO lessons VALUES (?,?,?)',(key,content,dt.datetime.now(dt.timezone.utc).isoformat()))
        db.execute('INSERT OR IGNORE INTO skills VALUES (?,?,?,?)',(key,content,'','lesson'))
        # Always ground a lesson in memory; link known related capabilities by tags.
        related={'memory'}
        related.update(name for name,(_,tags) in SKILLS.items() if any(word.casefold() in content.casefold() for word in tags.split()))
        db.executemany('INSERT OR IGNORE INTO edges VALUES (?,?,?)',[(key,name,'informs') for name in related])
    return key

def snapshot(path=None):
    with connect(path) as db:
        return {'skills':[dict(zip(('id','title','tags','kind'),r)) for r in db.execute('SELECT * FROM skills')],
                'relations':[dict(zip(('source','target','relation'),r)) for r in db.execute('SELECT * FROM edges')],
                'outcomes':[dict(zip(('skill','attempts','successful'),r)) for r in db.execute('SELECT skill,COUNT(*),SUM(ok) FROM experience GROUP BY skill')]}

def forget_lesson(content,path=None):
    key='lesson:'+hashlib.sha256(content.strip().encode('utf-8')).hexdigest()[:20]
    with connect(path) as db:
        db.execute('DELETE FROM edges WHERE source=? OR target=?',(key,key))
        db.execute('DELETE FROM skills WHERE id=?',(key,))
        db.execute('DELETE FROM lessons WHERE id=?',(key,))

def register_skill(skill_id,title,tags,path=None):
    if not isinstance(skill_id,str) or not skill_id.startswith('learned:') or not isinstance(title,str):
        raise ValueError('معرّف أو عنوان المهارة غير صالح')
    if not isinstance(tags,list) or any(not isinstance(tag,str) for tag in tags):
        raise ValueError('وسوم المهارة غير صالحة')
    normalized={tag.strip().casefold() for tag in tags if tag.strip()}
    related={'memory'}
    related.update(
        name for name,(_,known_tags) in SKILLS.items()
        if any(tag in known_tags.casefold().split() for tag in normalized)
    )
    with connect(path) as db:
        db.execute('INSERT INTO skills VALUES (?,?,?,?)',
                   (skill_id,title,','.join(sorted(normalized)),'learned'))
        db.executemany('INSERT OR IGNORE INTO edges VALUES (?,?,?)',
                       [(skill_id,name,'informs') for name in related])
    return skill_id

def remove_skill(skill_id,path=None):
    if not isinstance(skill_id,str) or not skill_id.startswith('learned:'):
        raise ValueError('يمكن حذف المهارات المعتمدة فقط')
    with connect(path) as db:
        row=db.execute('SELECT kind FROM skills WHERE id=?',(skill_id,)).fetchone()
        if row is None:
            return False
        if row[0]!='learned':
            raise ValueError('لا يمكن حذف مهارة أساسية من خلال هذا المسار')
        db.execute('DELETE FROM edges WHERE source=? OR target=?',(skill_id,skill_id))
        db.execute('DELETE FROM skills WHERE id=?',(skill_id,))
    return True
