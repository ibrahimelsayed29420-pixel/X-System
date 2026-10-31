import base64
import json
from pathlib import Path
import secrets
import subprocess
import time
import urllib.request
import winsound

ROOT=Path(__file__).resolve().parents[1]
KEY=ROOT/'voicetut.key'
PYTHON=Path('D:/X-System/runtime/voicetut-venv/Scripts/python.exe')
BASE='http://127.0.0.1:18763'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def request(path, payload=None, timeout=5):
    token=KEY.read_text(encoding='ascii').strip()
    req=urllib.request.Request(BASE+path,
        data=None if payload is None else json.dumps(payload).encode('utf-8'),
        headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(req,timeout=timeout) as response:
        return response.read()


def ensure_started():
    if not KEY.exists():
        KEY.write_text(secrets.token_urlsafe(32),encoding='ascii')
    try:
        request('/health')
        return
    except Exception:
        pass
    if not PYTHON.is_file():
        raise RuntimeError('VoiceTut environment is missing')
    print('جارٍ تحميل صوت حسن المحلي لأول مرة؛ سيظل جاهزًا للطلبات التالية...',flush=True)
    with (ROOT/'voicetut-service.log').open('ab') as log:
        worker=subprocess.Popen([str(PYTHON),str(Path(__file__).with_name('voicetut_worker.py'))],
            cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
    deadline=time.monotonic()+300
    while time.monotonic()<deadline:
        if worker.poll() is not None:
            raise RuntimeError('تعذر تحميل حسن؛ تفاصيل التشغيل في voicetut-service.log')
        try:
            request('/health',timeout=2)
            return
        except Exception:
            time.sleep(0.5)
    # This process was started by this call and has not become ready.
    worker.terminate()
    raise TimeoutError('استغرق تحميل حسن أكثر من خمس دقائق.')


def tts(mode,text):
    if mode=='voices':
        return [{'name':'VoiceTut Hassan','language':'ar-EG'}]
    ensure_started()
    data=request('/speak',{'text':text},timeout=300)
    if data[:4]!=b'RIFF':
        raise RuntimeError('VoiceTut returned invalid audio')
    result={'voice':'VoiceTut Hassan','language':'ar-EG'}
    if mode=='render':result['wav_b64']=base64.b64encode(data).decode('ascii')
    elif mode=='speak':winsound.PlaySound(data,winsound.SND_MEMORY);result['status']='spoken'
    else:raise ValueError('Unknown TTS mode')
    return result
