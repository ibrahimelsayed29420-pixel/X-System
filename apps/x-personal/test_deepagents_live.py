import json
from pathlib import Path
import time
from deepagent_worker import execute

started=time.monotonic()
result=execute('ابحث عن الموقع الرسمي لدائرة الأراضي والتنظيم العقاري في عجمان واذكر الرابط فقط.',observe=True)
report={'ok':result.get('ok'),'elapsed_seconds':round(time.monotonic()-started,2),
        'reply':result.get('reply') if result.get('tools') else 'No tool-backed answer; invalid output suppressed.', 'tools':result.get('tools'),'sources':result.get('sources'),
        'model':'x-qwen-agent:latest','engine':'Deep Agents'}
Path(__file__).with_name('deepagents-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if not result.get('sources') or not any(c['name']=='search_public_web' and c['state']=='complete' for c in result.get('tools',[])):
    raise RuntimeError('The local model did not execute the requested research tool')
