import datetime as dt
import json
from pathlib import Path
from x_personal.workflow import run_workflow

result = run_workflow('Ajman real estate department official',limit=2)
report = {'tested_at':dt.datetime.now(dt.timezone.utc).isoformat(),
          'engine':'LangGraph + SQLite checkpoint + Agent-Reach',
          'run_id':result.get('run_id'),'status':result.get('status'),
          'report_path':result.get('report_path'),
          'sources':[s['url'] for s in result.get('sources',[])],
          'error':result.get('error')}
Path(__file__).with_name('workflow-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if result.get('status') == 'complete' else 1)
