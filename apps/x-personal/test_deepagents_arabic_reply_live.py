import json
from pathlib import Path
import time
import uuid
from x_personal.mind_runtime import request

started=time.monotonic()
result=request({'text':'رد بالمصري في جملة قصيرة: إزاي هتساعدني أرتب يوم شغلي؟ من غير بحث.',
                'model':'x-qwen-agent:latest','session':'test-arabic-'+uuid.uuid4().hex})
reply=result.get('reply','')
report={'ok':result.get('ok'),'reply':reply,'tools':result.get('tools'),
        'elapsed_seconds':round(time.monotonic()-started,2),'language_requested':'Arabic'}
Path(__file__).with_name('deepagents-arabic-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if not result.get('ok') or not any('\u0600'<=c<='\u06ff' for c in reply):raise RuntimeError('No Arabic reply')
if any(c['name']=='search_public_web' for c in result.get('tools',[])):raise RuntimeError('Unrequested web search executed')
