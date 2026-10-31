import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def enabled():
    path=ROOT/'deep-reasoning.json'
    return path.exists() and json.loads(path.read_text(encoding='utf-8')).get('enabled') is True

def model():
    config=json.loads((ROOT/'deep-reasoning.json').read_text(encoding='utf-8'))
    return config['model']

def respond(state,route=None):
    selected_route=route or {'agent':'workflow-orchestrator','skill':'planning','model':model()}
    payload={'text':state['text'],'model':selected_route['model'],'route':selected_route,
             'history':state.get('history',[]),
             'facts':state.get('facts',[]),'evidence':state.get('evidence')}
    env=os.environ.copy();env['PYTHONUTF8']='1';env['LANGSMITH_TRACING']='false';env['LANGCHAIN_TRACING_V2']='false'
    result=subprocess.run(['D:/X-System/runtime/deepagents-venv/Scripts/python.exe',str(ROOT/'deepagent_worker.py')],
        input=json.dumps(payload),text=True,encoding='utf-8',capture_output=True,timeout=210,env=env)
    try:output=json.loads(result.stdout)
    except ValueError:raise RuntimeError('محرك التفكير لم يرجع نتيجة صالحة') from None
    if not output.get('ok'):raise RuntimeError(output.get('error','فشل محرك التفكير'))
    return output
