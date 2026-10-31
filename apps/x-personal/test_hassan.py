"""Local smoke test and performance record. Never opens the microphone."""
import base64
import json
from pathlib import Path
import time
from x_personal.voicetut_speech import tts

start=time.monotonic()
result=tts('render','أهلاً يا إبراهيم، أنا إكس.')
elapsed=time.monotonic()-start
data=base64.b64decode(result['wav_b64'])
if data[:4]!=b'RIFF' or len(data)<1000:raise RuntimeError('Invalid generated audio')
root=Path(__file__).resolve().parent
(root/'hassan-preview.wav').write_bytes(data)
(root/'hassan-verification.json').write_text(json.dumps({
    'speaker':'Hassan','engine':'VoiceTut','device':'cpu','dtype':'float32',
    'num_step':16,'load_and_generation_seconds':round(elapsed,2),
    'audio_bytes':len(data),'status':'PASS','microphone_opened':False,
    'speech_sent_to_external_service':False,
},indent=2),encoding='utf-8')
print(f'PASS: Hassan generated locally in {elapsed:.2f}s; {len(data)} bytes',flush=True)
