import json
from pathlib import Path
import tempfile
import time
from semantic_worker import execute

start=time.monotonic()
with tempfile.TemporaryDirectory() as directory:
    facts=[{'id':1,'content':'إبراهيم يفضل الردود القصيرة بالمصري ويركز على عقارات عجمان'},
           {'id':2,'content':'يوم الجمعة إجازة من الشغل'}]
    result=execute('طريقة الكلام المفضلة لإبراهيم',facts,data_dir=directory)
    second=execute('طريقة الكلام المفضلة لإبراهيم',facts,data_dir=directory)
    report={'ok':result.get('ok'),'indexed_facts':result.get('indexed_facts'),
            'retrieved':result.get('items'),'repeat_indexed_facts':second.get('indexed_facts'),
            'elapsed_seconds':round(time.monotonic()-start,2),'loopback_only':True}
Path(__file__).with_name('semantic-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if not result.get('items'):raise RuntimeError('Semantic recall returned no memories')
