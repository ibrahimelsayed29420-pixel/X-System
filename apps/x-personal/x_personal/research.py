"""Public research integrated into X; results retain their source URLs."""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
PYTHON = Path('D:/X-System/runtime/agent-reach-venv/Scripts/python.exe')

def research(channel, action, value, limit=5):
    if channel not in ('web', 'github', 'youtube') or action not in ('search', 'read'):
        raise ValueError('قناة البحث أو الإجراء غير مدعوم')
    if not value.strip() or len(value) > 2000 or not 1 <= limit <= 10:
        raise ValueError('اكتب طلب بحث وحدد عدد نتائج بين 1 و10')
    env = os.environ.copy()
    env['PYTHONUTF8'] = '1'
    for name in ('GH_TOKEN', 'GITHUB_TOKEN', 'OPENAI_API_KEY', 'GROQ_API_KEY'):
        env.pop(name, None)
    result = subprocess.run([str(PYTHON), str(ROOT / 'reach_worker.py')],
        input=json.dumps(dict(channel=channel, action=action, value=value, limit=limit)),
        text=True, encoding='utf-8', capture_output=True, timeout=45, env=env, cwd=str(ROOT))
    try:
        payload = json.loads(result.stdout)
    except ValueError:
        raise RuntimeError('تعذر تشغيل أداة البحث؛ راجع تثبيت Agent-Reach') from None
    return payload
