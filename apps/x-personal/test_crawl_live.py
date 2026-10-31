import json
from pathlib import Path
import time
from x_personal.public_pages import read_public_page

started=time.monotonic()
result=read_public_page('https://example.com/')
report={'ok':result.get('ok'),'url':result.get('url'),'title':result.get('title'),
        'characters':result.get('characters'),'sample':result.get('text','')[:450],
        'elapsed_seconds':round(time.monotonic()-started,2),'error':result.get('error')}
Path(__file__).with_name('crawl-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if (not result.get('ok') or result.get('title')!='Example Domain'
        or 'This domain is for use in documentation examples' not in result.get('text','')):
    raise RuntimeError('Live page read did not pass')
