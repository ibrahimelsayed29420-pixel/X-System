import json
from pathlib import Path
import time
import uuid
from x_personal.mind_runtime import request

started=time.monotonic()
result=request({'text':'In English, give me one short sentence explaining how you can help organize my working day. Do not search the web.',
                'model':'x-qwen-agent:latest','session':'test-bilingual-'+uuid.uuid4().hex})
report={'ok':result.get('ok'),'reply':result.get('reply'),'tools':result.get('tools'),
        'elapsed_seconds':round(time.monotonic()-started,2),'language_requested':'English'}
Path(__file__).with_name('deepagents-english-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if not result.get('reply') or not any('a'<=c.lower()<='z' for c in result['reply']):raise RuntimeError('No English response')
if any(c['name']=='search_public_web' for c in result.get('tools',[])):raise RuntimeError('Unrequested web search executed')
