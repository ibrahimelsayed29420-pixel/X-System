"""Per-user background mind with a read-only loopback dashboard; no desktop capture."""
import ctypes
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from x_personal.mind_runtime import DATA,ROOT
from x_personal import learning,skill_graph

def atomic(path,value):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    for attempt in range(20):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt==19:raise
            time.sleep(.025)

def state(value,request_id=None):
    atomic(DATA/'status.json',{'pid':os.getpid(),'state':value,'request_id':request_id,
           'updated_at':dt.datetime.now(dt.timezone.utc).isoformat(),
           'scope':'X requests and explicit lessons only; no desktop monitoring'})

def execute(envelope):
    request_id=str(uuid.UUID(envelope['id']))
    payload=envelope['payload']
    from x_personal.memory import validate_session
    validate_session(payload['session'])
    if not isinstance(payload.get('text'),str) or not 1<=len(payload['text'])<=4000:
        raise ValueError('Invalid conversation input')
    from x_personal.identity import load_settings, require_identity
    require_identity()
    # Model is a local configuration choice, not arbitrary request-supplied code.
    payload['model']=load_settings()['ollama_model']
    state('processing',request_id)
    env=os.environ.copy();env['PYTHONUTF8']='1'
    env['LANGCHAIN_TRACING_V2']='false';env['LANGSMITH_TRACING']='false'
    env['X_REQUEST_ID']=request_id
    for key in ('LANGSMITH_API_KEY','LANGCHAIN_API_KEY'):env.pop(key,None)
    process=subprocess.run(['D:/X-System/runtime/x-workflow-venv/Scripts/python.exe',str(ROOT/'mind_worker.py')],
        input=json.dumps(payload),text=True,encoding='utf-8',capture_output=True,
        timeout=330,env=env,cwd=str(ROOT),creationflags=subprocess.CREATE_NO_WINDOW)
    result=json.loads(process.stdout)
    route=result.get('route') or {}
    routed_skill=route.get('skill') or result.get('intent','chat')
    skill_graph.record(request_id,routed_skill,result.get('ok'),str(result.get('error','')))
    learning.record_x_activity(request_id,routed_skill,result.get('tools',[]),
                               result.get('ok') is True)
    if any(c.get('name')=='search_public_web' and c.get('state')=='complete' for c in result.get('tools',[])):
        skill_graph.record(request_id+':research','search',True)
    return result

def main():
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_bool,ctypes.c_wchar_p]
    kernel.CreateMutexW.restype=ctypes.c_void_p
    mutex=kernel.CreateMutexW(None,False,'Local\\XMindBackgroundIbrahim')
    if not mutex or ctypes.get_last_error()==183:return
    from x_personal.mind_runtime import migrate_legacy_data
    migrate_legacy_data()
    DATA.mkdir(parents=True,exist_ok=True)
    for name in ('inbox','results'):(DATA/name).mkdir(exist_ok=True)
    skill_graph.snapshot()
    # Revisit only this service's interrupted claimed requests after a restart.
    for claimed in (DATA/'inbox').glob('*.working'):
        claimed.replace(claimed.with_suffix('.json'))
    state('ready')
    import threading
    from mind_dashboard import serve
    threading.Thread(target=serve,daemon=True).start()
    try:
        while not (DATA/'stop.request').exists():
            pending=sorted((DATA/'inbox').glob('*.json'))
            if not pending:
                state('ready');time.sleep(2);continue
            for path in pending:
                try:
                    request_id=str(uuid.UUID(path.stem))
                except ValueError:
                    path.replace(path.with_suffix('.rejected'))
                    continue
                claimed=path.with_suffix('.working');path.replace(claimed)
                if (DATA/'results'/(request_id+'.json')).exists():
                    claimed.unlink()
                    continue
                try:
                    if claimed.stat().st_size>24000:raise ValueError('Request too large')
                    envelope=json.loads(claimed.read_text(encoding='utf-8'))
                    if envelope.get('id')!=request_id:raise ValueError('Request ID mismatch')
                    result=execute(envelope)
                except Exception as exc:
                    result={'ok':False,'error':str(exc)[:500]}
                atomic(DATA/'results'/(request_id+'.json'),result)
                claimed.unlink()
                state('ready')
                if (DATA/'stop.request').exists():break
    finally:
        (DATA/'stop.request').unlink(missing_ok=True)
        state('stopped')

if __name__=='__main__':
    try:main()
    except Exception:
        import traceback
        DATA.mkdir(parents=True,exist_ok=True)
        with (DATA/'runtime-errors.log').open('a',encoding='utf-8') as log:
            log.write(traceback.format_exc())
        raise
