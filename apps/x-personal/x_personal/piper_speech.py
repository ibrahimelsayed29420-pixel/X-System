"""Local neural Arabic voice; no voice cloning or network inference."""
import base64
import io
import wave
import winsound
from pathlib import Path

MODEL = Path('D:/X-System/models/tts/piper/ar_JO-kareem-medium.onnx')
_voice = None


def tts(mode, text):
    global _voice
    if mode == 'voices':
        return [{'name': 'Piper Kareem medium', 'language': 'ar-JO'}] if MODEL.is_file() else []
    if not text.strip() or len(text) > 4000:
        raise ValueError('Speech text must be 1..4000 characters.')
    from piper import PiperVoice, SynthesisConfig
    if _voice is None:
        _voice = PiperVoice.load(str(MODEL))
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as stream:
        _voice.synthesize_wav(text, stream, syn_config=SynthesisConfig(length_scale=0.95))
    audio = buffer.getvalue()
    result = {'voice':'Piper Kareem medium','language':'ar-JO'}
    if mode == 'render':
        result['wav_b64'] = base64.b64encode(audio).decode('ascii')
    elif mode == 'speak':
        winsound.PlaySound(audio, winsound.SND_MEMORY)
        result['status'] = 'spoken'
    else:
        raise ValueError('Unknown TTS mode')
    return result
