"""Run X's pinned local workflow engine in its own Python environment."""
import json
import os
from pathlib import Path
import subprocess
import uuid

ROOT = Path(__file__).resolve().parent.parent
PYTHON = Path('D:/X-System/runtime/x-workflow-venv/Scripts/python.exe')

def run_workflow(query='', channel='web', limit=3, resume=None):
    if resume:
        uuid.UUID(resume)
    elif not query.strip() or len(query) > 2000:
        raise ValueError('اكتب طلب بحث من 1 إلى 2000 حرف')
    if channel not in ('web', 'github', 'youtube') or not 1 <= limit <= 10:
        raise ValueError('قناة أو عدد نتائج غير صالح')
    env = os.environ.copy()
    env['PYTHONUTF8'] = '1'
    env['LANGCHAIN_TRACING_V2'] = 'false'
    env['LANGSMITH_TRACING'] = 'false'
    for key in ('LANGSMITH_API_KEY', 'LANGCHAIN_API_KEY'):
        env.pop(key, None)
    process = subprocess.run([str(PYTHON), str(ROOT / 'workflow_worker.py')],
        input=json.dumps(dict(query=query, channel=channel, limit=limit, resume=resume)),
        text=True, encoding='utf-8', capture_output=True, timeout=100, env=env, cwd=str(ROOT))
    try:
        return json.loads(process.stdout)
    except ValueError:
        raise RuntimeError('تعذر تشغيل مسار X؛ راجع تثبيت محرك المهام') from None
