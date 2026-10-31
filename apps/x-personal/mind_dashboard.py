"""Read-only loopback dashboard of observed X runtime state."""
import json
import io
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import wave
from urllib.parse import urlsplit
from x_personal import brain
from x_personal.identity import load_settings,require_identity
from x_personal.mind_runtime import DATA,ROOT,status,alive
from x_personal import learning
from x_personal.skill_graph import snapshot

def read(path,default):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):return default

def observed():
    events=[]
    path=DATA/'events.jsonl'
    if path.exists():
        with path.open('rb') as stream:
            stream.seek(max(0,path.stat().st_size-24000))
            for line in stream.read().decode('utf-8',errors='replace').splitlines():
                try:events.append(json.loads(line))
                except ValueError:pass
    stage=read(DATA/'stage.json',{})
    stage['worker_alive']=alive(stage.get('worker_pid')) if stage.get('worker_pid') else False
    return {'runtime':status(),'stage':stage,
            'chat_available':True,
            'graph':snapshot(),'events':events[-30:],
            'learning':learning.snapshot(),
            'pending':len(list((DATA/'inbox').glob('*.json'))),
            'results':len(list((DATA/'results').glob('*.json'))),
            'semantic':read(ROOT/'semantic-memory.json',{}),
            'agent':read(DATA/'agent-trace.json',{}),
            'reasoning':read(ROOT/'deep-reasoning.json',{}),
            'verification':read(ROOT/'identity-policy.json',{}).get('verification_required',True),
            'observation_scope':'X requests only; no screen, microphone or other-app monitoring'}

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass

    def _allowed_request(self,require_origin=False):
        port=self.server.server_port
        allowed_hosts={f'127.0.0.1:{port}',f'localhost:{port}'}
        allowed_origins={f'http://{host}' for host in allowed_hosts}
        host=self.headers.get('Host','')
        origin=self.headers.get('Origin')
        return host in allowed_hosts and (
            origin in allowed_origins if require_origin
            else not origin or origin in allowed_origins
        )

    def _json(self,value,status_code=200):
        body=json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError):pass

    def _learning_action(self,action,data):
        if action=='set_capture':
            return {'capture_x_activity':learning.set_activity_capture(data.get('enabled'))}
        if action=='add_folder':
            source_id=learning.add_folder_source(data.get('folder'),data.get('own_materials'))
            return {'source_id':source_id}
        if action=='scan_source':
            return learning.scan_source(data.get('source_id'))
        if action=='revoke_source':
            learning.revoke_source(data.get('source_id'))
            return {'removed':True}
        if action=='approve_proposal':
            return learning.approve_proposal(data.get('proposal_id'))
        if action=='reject_proposal':
            learning.reject_proposal(data.get('proposal_id'))
            return {'removed':True}
        if action=='remove_skill':
            learning.remove_approved_skill(data.get('skill_id'))
            return {'removed':True}
        raise ValueError('إجراء التعلم غير معروف')

    def do_GET(self):
        if not self._allowed_request():
            self.send_error(403);return
        path=urlsplit(self.path).path
        if path=='/favicon.ico':
            self.send_response(204);self.end_headers();return
        if path=='/api/state':
            body=json.dumps(observed(),ensure_ascii=False).encode('utf-8');content_type='application/json; charset=utf-8'
        elif path in ('/','/index.html'):
            body=(ROOT/'mind-live.html').read_bytes();content_type='text/html; charset=utf-8'
        else:self.send_error(404);return
        self.send_response(200)
        self.send_header('Content-Type',content_type)
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.send_header('Content-Length',str(len(body)));self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError):pass

    def _chat(self,data):
        if not isinstance(data,dict) or not isinstance(data.get('text'),str):
            raise ValueError('اكتب رسالتك قبل الإرسال.')
        text=data['text'].strip()
        if not 1<=len(text)<=4000:
            raise ValueError('الرسالة يجب أن تكون من 1 إلى 4000 حرف.')
        settings=load_settings()
        reply=brain.answer(text,settings['ollama_model'])
        return {'ok':True,'reply':reply}

    def _transcribe(self,audio_data):
        if not audio_data or len(audio_data)>4_000_000:
            raise ValueError('حجم التسجيل غير صالح؛ الحد الأقصى دقيقتان.')
        try:
            with wave.open(io.BytesIO(audio_data),'rb') as audio:
                if (audio.getcomptype()!='NONE' or audio.getsampwidth()!=2
                        or audio.getnchannels()!=1 or audio.getframerate()!=16000):
                    raise ValueError('تنسيق الصوت غير مدعوم؛ أعد التسجيل من زر الميكروفون.')
                frames=audio.getnframes()
                if not 1<=frames<=16000*120:
                    raise ValueError('مدة التسجيل يجب أن تكون أقل من دقيقتين.')
                pcm=audio.readframes(frames)
                if len(pcm)!=frames*2:
                    raise ValueError('ملف الصوت غير مكتمل.')
        except wave.Error as exc:
            raise ValueError('تعذر قراءة ملف الصوت؛ أعد التسجيل.') from exc
        require_identity()
        import numpy as np
        from x_personal.speech import ArabicListener
        listener=ArabicListener(load_settings())
        transcript=listener.transcribe(np.frombuffer(pcm,dtype=np.int16).astype(np.float32)/32768.0,16000)
        return {'ok':True,'text':transcript}

    def do_POST(self):
        if not self._allowed_request(require_origin=True):
            self.send_error(403);return
        path=urlsplit(self.path).path
        if path not in ('/api/learning','/api/chat','/api/transcribe'):
            self.send_error(404);return
        if path=='/api/transcribe':
            if self.headers.get('Content-Type','').split(';',1)[0].strip().lower()!='audio/wav':
                self._json({'error':'يجب إرسال تسجيل WAV محلي'},415);return
            try:
                length=int(self.headers.get('Content-Length',''))
            except ValueError:
                self._json({'error':'حجم التسجيل غير صالح'},400);return
            if not 1<=length<=4_000_000:
                self._json({'error':'حجم التسجيل يجب أن يكون بين 1 و4000000 بايت'},413);return
            try:
                result=self._transcribe(self.rfile.read(length))
            except PermissionError as exc:
                self._json({'error':str(exc)},403);return
            except (ValueError,TypeError) as exc:
                self._json({'error':str(exc)},400);return
            except Exception as exc:
                self._json({'error':str(exc)[:500]},502);return
            self._json(result);return
        if self.headers.get('Content-Type','').split(';',1)[0].strip().lower()!='application/json':
            self._json({'error':'يجب إرسال طلب JSON'},415);return
        try:
            length=int(self.headers.get('Content-Length',''))
        except ValueError:
            self._json({'error':'حجم الطلب غير صالح'},400);return
        max_length=24000 if path=='/api/chat' else 16384
        if not 1<=length<=max_length:
            self._json({'error':f'حجم الطلب يجب أن يكون بين 1 و{max_length} بايت'},413);return
        try:
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict) or (path!='/api/chat' and not isinstance(data.get('action'),str)):
                raise ValueError('بيانات الإجراء غير صالحة')
            if path=='/api/chat':
                result=self._chat(data)
            else:
                result=self._learning_action(data['action'],data)
        except (ValueError,TypeError) as exc:
            self._json({'error':str(exc)},400);return
        except PermissionError as exc:
            self._json({'error':str(exc)},403);return
        except RuntimeError as exc:
            self._json({'error':str(exc)},502);return
        self._json({'ok':True,'result':result})

def serve():
    ThreadingHTTPServer(('127.0.0.1',18764),Handler).serve_forever()


if __name__=='__main__':
    serve()
