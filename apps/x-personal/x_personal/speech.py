"""Local Arabic speech. No cloud calls, disk recording or background listening."""
import base64
import json
import queue
import subprocess
import msvcrt
from pathlib import Path


def tts(mode='voices', text=''):
    from .identity import load_settings
    if load_settings().get('tts_backend') == 'voicetut':
        from .voicetut_speech import tts as hassan_tts
        return hassan_tts(mode,text)
    if load_settings().get('tts_backend') == 'piper':
        from .piper_speech import tts as piper_tts
        return piper_tts(mode, text)
    payload = json.dumps({'text_b64': base64.b64encode(text.encode('utf-8')).decode('ascii')})
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File',
                             str(Path(__file__).with_name('tts.ps1')), '-Mode', mode],
                            input=payload, capture_output=True, text=True, encoding='utf-8',
                            timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or 'Windows speech synthesis failed.')
    return json.loads(result.stdout.lstrip('\ufeff'))


def ArabicListener(settings):
    if settings.get('speech_backend', 'vosk') == 'sherpa-onnx':
        from .onnx_speech import OnnxArabicListener
        return OnnxArabicListener(settings)
    return VoskArabicListener(settings)


class VoskArabicListener:
    def __init__(self, settings):
        from vosk import Model, SetLogLevel
        model_dir = Path(settings['vosk_model'])
        if not (model_dir / 'am/final.mdl').is_file():
            raise RuntimeError('نموذج الاستماع غير موجود. شغّل Download-Speech-Model.ps1 أولًا.')
        SetLogLevel(-1)
        self.model = Model(str(model_dir))
        self.device = settings.get('microphone_device')

    def listen_once(self):
        import sounddevice as sd
        from vosk import KaldiRecognizer
        audio = queue.Queue(maxsize=100)
        overflow = []
        device_info = sd.query_devices(self.device, 'input')
        rate = int(device_info['default_samplerate'])
        recognizer = KaldiRecognizer(self.model, rate)
        recognizer.SetWords(False)

        def callback(data, frames, timing, status):
            if status:
                overflow.append(str(status))
            try:
                audio.put_nowait(bytes(data))
            except queue.Full:
                overflow.append('audio_queue_full')

        parts = []
        input('جاهز. اضغط Enter لبدء التسجيل...')
        with sd.RawInputStream(samplerate=rate, blocksize=max(800, rate // 5), device=self.device,
                               dtype='int16', channels=1, callback=callback):
            print('● التسجيل شغّال — اتكلم براحتك، واضغط Enter لإنهائه. Ctrl+C للإلغاء.', flush=True)
            while True:
                if msvcrt.kbhit():
                    key = msvcrt.getwch()
                    if key == '\x03':
                        raise KeyboardInterrupt
                    if key == '\r':
                        break
                try:
                    data = audio.get(timeout=0.2)
                except queue.Empty:
                    continue
                if recognizer.AcceptWaveform(data):
                    parts.append(json.loads(recognizer.Result()).get('text', ''))
        print('■ انتهى التسجيل. جارٍ استخراج النص...', flush=True)
        while not audio.empty():
            if recognizer.AcceptWaveform(audio.get_nowait()):
                parts.append(json.loads(recognizer.Result()).get('text', ''))
        parts.append(json.loads(recognizer.FinalResult()).get('text', ''))
        if overflow:
            raise RuntimeError('انقطع جزء من الصوت؛ أعد المحاولة بدل اعتماد أمر ناقص.')
        return ' '.join(p for p in parts if p).strip()
