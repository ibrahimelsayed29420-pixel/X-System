import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def retrieve(query,facts):
    config_path=ROOT/'semantic-memory.json'
    if not config_path.exists() or not json.loads(config_path.read_text(encoding='utf-8')).get('enabled'):
        return {'ok':False,'items':[],'state':'not_enabled'}
    if not facts:return {'ok':True,'items':[],'state':'no_saved_facts'}
    try:
        process=subprocess.run(['D:/X-System/runtime/mem0-venv/Scripts/python.exe',str(ROOT/'semantic_worker.py')],
            input=json.dumps({'query':query,'facts':facts}),capture_output=True,text=True,encoding='utf-8',timeout=75)
        return json.loads(process.stdout)
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
        return {'ok':False,'items':[],'state':'unavailable','error':str(exc)[:200]}
