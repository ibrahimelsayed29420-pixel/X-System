"""File-queue client for X's per-user Windows background runtime."""
import ctypes
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
LOCAL_APP_DATA=Path(os.environ.get('LOCALAPPDATA') or Path.home()/'AppData'/'Local')
APP_DATA=Path(os.environ.get('X_MIND_HOME') or LOCAL_APP_DATA/'X-System'/'mind')
DATA=APP_DATA/'runtime'
LEGACY_APP_DATA=Path('D:/X-System/data/mind')
LEGACY_DATA=LEGACY_APP_DATA/'runtime'
_SAFE_REQUEST_FILE=re.compile(
    r'^(?:[0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
    r'[0-9a-f]{4}-[0-9a-f]{12})\.(?:json|working)$'
)
_MAX_MIGRATED_FILE_BYTES=10*1024*1024


def _is_reparse_point(path):
    details=path.lstat()
    return stat.S_ISLNK(details.st_mode) or bool(
        getattr(details,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400)
    )


def _copy_once(source,destination):
    if destination.exists() or not source.is_file() or _is_reparse_point(source):
        return False
    if source.stat().st_size>_MAX_MIGRATED_FILE_BYTES:
        return False
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_name(destination.name+'.'+uuid.uuid4().hex+'.migration')
    try:
        with source.open('rb') as incoming,temporary.open('xb') as outgoing:
            shutil.copyfileobj(incoming,outgoing)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return True


def _migrate_learning_database(source,destination):
    if destination.exists() or not source.is_file() or _is_reparse_point(source):
        return False
    destination.parent.mkdir(parents=True,exist_ok=True)
    uri=source.resolve().as_uri()+'?mode=ro'
    source_db=sqlite3.connect(uri,uri=True,timeout=10)
    target_db=sqlite3.connect(str(destination),timeout=10)
    try:
        source_db.backup(target_db)
    except Exception:
        target_db.close()
        destination.unlink(missing_ok=True)
        raise
    else:
        target_db.close()
    finally:
        source_db.close()
    return True


def migrate_legacy_data(app_data=None,legacy_app_data=None):
    target_root=Path(app_data or APP_DATA)
    source_root=Path(legacy_app_data or LEGACY_APP_DATA)
    target_runtime=target_root/'runtime'
    source_runtime=source_root/'runtime'
    target_runtime.mkdir(parents=True,exist_ok=True)

    for name in ('events.jsonl','stage.json','agent-trace.json','runtime-errors.log'):
        _copy_once(source_runtime/name,target_runtime/name)

    for directory in ('inbox','results'):
        old_directory=source_runtime/directory
        if not old_directory.is_dir() or _is_reparse_point(old_directory):
            continue
        for source in old_directory.iterdir():
            if _SAFE_REQUEST_FILE.fullmatch(source.name):
                if directory=='inbox':
                    # Preserve old requests for review; never execute them just because paths changed.
                    destination=target_runtime/'recovered'/'inbox'/(source.name+'.paused')
                else:
                    destination=target_runtime/directory/source.name
                _copy_once(source,destination)

    _migrate_learning_database(
        source_runtime/'learning.sqlite',
        target_root/'learning.sqlite',
    )

    old_skills=source_root/'skills'/'approved'
    new_skills=target_root/'skills'/'approved'
    if old_skills.is_dir() and not _is_reparse_point(old_skills):
        for old_directory in old_skills.iterdir():
            if (not re.fullmatch(r'learned-[0-9a-f]{12}',old_directory.name)
                    or not old_directory.is_dir() or _is_reparse_point(old_directory)):
                continue
            source=old_directory/'SKILL.md'
            if source.is_file() and not _is_reparse_point(source) and source.stat().st_size<=10000:
                _copy_once(source,new_skills/old_directory.name/'SKILL.md')

    return {'runtime':str(target_runtime),'learning':str(target_root/'learning.sqlite'),
            'approved_skills':str(new_skills)}

def alive(pid):
    if not pid:return False
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_bool,ctypes.c_uint32]
    kernel.OpenProcess.restype=ctypes.c_void_p
    kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)]
    kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=kernel.OpenProcess(0x1000,False,int(pid))
    if not handle:return False
    try:
        code=ctypes.c_uint32()
        return bool(kernel.GetExitCodeProcess(handle,ctypes.byref(code))) and code.value==259
    finally:kernel.CloseHandle(handle)

def status():
    try:
        result=json.loads((DATA/'status.json').read_text(encoding='utf-8'))
        result['process_alive']=alive(result.get('pid'))
        return result
    except FileNotFoundError:
        return {'state':'stopped','process_alive':False}
    except (OSError,ValueError) as exc:
        raise RuntimeError(f'تعذر قراءة حالة عقل X من {DATA}: {exc}') from exc

def ensure_started():
    if status().get('process_alive'):return
    DATA.mkdir(parents=True,exist_ok=True)
    subprocess.Popen(['D:/X-System/runtime/x-personal-venv/Scripts/pythonw.exe',str(ROOT/'mind_service.py')],
                     cwd=str(ROOT),creationflags=subprocess.CREATE_NO_WINDOW)
    for _ in range(50):
        if status().get('process_alive'):return
        time.sleep(.1)
    raise RuntimeError('تعذر بدء عقل X في الخلفية')

def request(payload,timeout=350):
    ensure_started()
    request_id=str(uuid.uuid4())
    inbox=DATA/'inbox';inbox.mkdir(exist_ok=True)
    envelope={'id':request_id,'submitted_at':dt.datetime.now(dt.timezone.utc).isoformat(),'payload':payload}
    temporary=inbox/(request_id+'.tmp')
    temporary.write_text(json.dumps(envelope,ensure_ascii=False),encoding='utf-8')
    temporary.replace(inbox/(request_id+'.json'))
    output=DATA/'results'/(request_id+'.json')
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if output.exists():return json.loads(output.read_text(encoding='utf-8'))
        if not status().get('process_alive'):raise RuntimeError('توقف عقل X قبل إنهاء الطلب')
        time.sleep(.2)
    raise TimeoutError('انتهت مهلة انتظار X؛ الطلب مسجل ويمكن مراجعة نتيجته عند اكتماله')
