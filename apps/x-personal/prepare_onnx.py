"""Validate and extract the official Sherpa Whisper base model, then smoke test."""
import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile
import time
import wave
import numpy as np
from x_personal.onnx_speech import OnnxArabicListener
from x_personal.speech import tts

root = Path('D:/X-System/models/speech')
archive = root / 'sherpa-onnx-whisper-base.tar.bz2'
target = root / 'sherpa-onnx-whisper-base'
with tarfile.open(archive) as tar:
    for item in tar.getmembers():
        parts = Path(item.name.replace('\\', '/')).parts
        if item.issym() or item.islnk() or item.isdev() or '..' in parts or ':' in item.name:
            raise ValueError('Unsafe model archive entry')
        if not parts or parts[0] != target.name:
            raise ValueError('Unexpected archive root')
    tar.extractall(root, filter='data')
listener = OnnxArabicListener({'onnx_model': str(target)})
assert listener.transcribe(np.zeros(16000, dtype=np.float32), 16000) == ''
render = tts('render', 'أنا اسمي إبراهيم، وعندي ثلاث مكالمات واجتماع الساعة خمسة.')
with wave.open(io.BytesIO(base64.b64decode(render['wav_b64']))) as wav:
    assert wav.getsampwidth() == 2
    rate = wav.getframerate()
    data = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
    if wav.getnchannels() > 1:
        data = data.reshape(-1, wav.getnchannels()).mean(axis=1)
samples = data.astype(np.float32) / 32768
start = time.monotonic()
text = listener.transcribe(samples, rate)
if not text:
    raise RuntimeError('Synthetic Arabic smoke test returned no text; backend was not enabled.')
report = {'backend': 'sherpa-onnx', 'model': 'whisper-base-int8-multilingual',
          'provider': 'cpu', 'python_platform': 'win-amd64',
          'silence_gate': 'PASS', 'synthetic_arabic_text': text,
          'decode_seconds': round(time.monotonic()-start, 2),
          'microphone_opened': False, 'egyptian_human_speech_quality': 'NOT_YET_MEASURED',
          'archive_sha256_local': hashlib.sha256(archive.read_bytes()).hexdigest(),
          'source': 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-base.tar.bz2'}
Path(__file__).with_name('onnx-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
settings_path = Path(__file__).with_name('settings.json')
settings = json.loads(settings_path.read_text(encoding='utf-8-sig'))
backup = settings_path.with_name('settings.before-onnx.json')
if not backup.exists():
    backup.write_text(json.dumps(settings,ensure_ascii=False,indent=2),encoding='utf-8')
settings.update(speech_backend='sherpa-onnx', onnx_model=str(target))
settings_path.write_text(json.dumps(settings,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
