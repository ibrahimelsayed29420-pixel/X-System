import json
from pathlib import Path
import time
import uuid
from x_personal.mind_runtime import request,status

start=time.monotonic()
result=request({'text':'إنت اسمك إيه؟ في جملة واحدة بالمصري.','model':'x-ibrahim:latest','session':'test-runtime-'+uuid.uuid4().hex})
report={'ok':result.get('ok'),'reply':result.get('reply'),'elapsed_seconds':round(time.monotonic()-start,2),
        'runtime':status(),'error':result.get('error')}
Path(__file__).with_name('runtime-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if result.get('ok') else 1)
