"""Persistent local Hassan voice service. No camera, mic or account access."""
import io
import faulthandler
import json
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path('D:/X-System/apps/x-personal')
KEY = ROOT / 'voicetut.key'
PORT = 18763


def main():
    faulthandler.enable()
    faulthandler.dump_traceback_later(60,repeat=True)
    print('Importing local voice libraries',flush=True)
    import torch
    import soundfile as sf
    from voicetut_tts import VoiceTutTTS
    print('Voice libraries imported',flush=True)
    torch.set_num_threads(4)
    token = KEY.read_text(encoding='ascii').strip()
    (ROOT/'voice-runtime.json').write_text(json.dumps({'pid':os.getpid(),'stage':'loading'}),encoding='utf-8')
    voice = VoiceTutTTS.from_pretrained('D:/X-System/models/tts/voicetut', device='cpu', dtype='float32')
    faulthandler.cancel_dump_traceback_later()
    generation_lock=threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Do not record conversation text.

        def authorized(self):
            return secrets.compare_digest(self.headers.get('Authorization',''), 'Bearer '+token)

        def do_GET(self):
            if self.path != '/health' or not self.authorized():
                self.send_error(403)
                return
            body=b'{"ready":true,"speaker":"Hassan"}'
            self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)

        def do_POST(self):
            if self.path == '/stop' and self.authorized():
                self.send_response(200);self.end_headers();self.wfile.write(b'OK')
                threading.Thread(target=self.server.shutdown,daemon=True).start()
                return
            if self.path != '/speak' or not self.authorized():
                self.send_error(403);return
            size=int(self.headers.get('Content-Length','0'))
            if not 0 < size <= 20000:
                self.send_error(413);return
            if not generation_lock.acquire(blocking=False):
                self.send_error(429,'Voice generation is busy');return
            try:
                text=json.loads(self.rfile.read(size))['text']
                if not isinstance(text,str) or not 0 < len(text.strip()) <= 2000:
                    raise ValueError('Expected 1..2000 characters')
                (ROOT/'voice-runtime.json').write_text(json.dumps({'pid':os.getpid(),'stage':'generating'}),encoding='utf-8')
                audio=voice.synthesize(text, speaker='Hassan', num_step=16, speed=1.0)
                output=io.BytesIO()
                sf.write(output,audio,voice.sampling_rate,format='WAV',subtype='PCM_16')
                body=output.getvalue()
                self.send_response(200);self.send_header('Content-Type','audio/wav');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
            except Exception as exc:
                self.send_error(500, type(exc).__name__)
            finally:
                (ROOT/'voice-runtime.json').write_text(json.dumps({'pid':os.getpid(),'stage':'ready'}),encoding='utf-8')
                generation_lock.release()

    print('Hassan voice loaded on CPU', flush=True)
    (ROOT/'voice-runtime.json').write_text(json.dumps({'pid':os.getpid(),'stage':'ready'}),encoding='utf-8')
    ThreadingHTTPServer(('127.0.0.1',PORT),Handler).serve_forever()


if __name__ == '__main__':
    os.environ.setdefault('HF_HOME','D:/X-System/models/huggingface')
    os.environ.setdefault('HF_HUB_DISABLE_XET','1')
    os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY','1')
    os.environ['HF_HUB_OFFLINE']='1'
    main()
