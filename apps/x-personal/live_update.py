"""Record an observed task state for the local live board."""
import datetime
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parent
path=root/'live-activity.json'
old=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
item={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'message':sys.argv[1] if len(sys.argv)>1 else 'تحديث الحالة',
      'state':sys.argv[2] if len(sys.argv)>2 else 'running'}
events=(old.get('events',[])+[item])[-40:]
temporary=path.with_suffix('.tmp')
temporary.write_text(json.dumps({**item,'events':events},ensure_ascii=False,indent=2),encoding='utf-8')
temporary.replace(path)
