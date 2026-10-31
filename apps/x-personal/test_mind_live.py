import datetime as dt
import json
from pathlib import Path
import time
import uuid
from x_personal import brain

started=time.monotonic()
reply=brain.answer('إنت مين واسمك إيه؟ ورد عليا بالمصري في سطر واحد.', 'x-ibrahim:latest', 'test-'+uuid.uuid4().hex)
report={'tested_at':dt.datetime.now(dt.timezone.utc).isoformat(), 'model':'x-ibrahim:latest',
        'elapsed_seconds':round(time.monotonic()-started,2),'reply':reply,'response_received':bool(reply),
        'note':'Live response test only, not proof of Egyptian dialect quality or factual reliability.'}
Path(__file__).with_name('mind-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
