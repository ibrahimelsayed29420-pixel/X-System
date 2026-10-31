"""Arabic Whisper through Sherpa-ONNX; local CPU inference."""
import msvcrt
import queue
from pathlib import Path


class OnnxArabicListener:
    def __init__(self, settings):
        import sherpa_onnx
        root = Path(settings['onnx_model'])
        self.recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=str(root / 'base-encoder.int8.onnx'),
            decoder=str(root / 'base-decoder.int8.onnx'),
            tokens=str(root / 'base-tokens.txt'),
            language='ar', task='transcribe', num_threads=4, provider='cpu',
        )
        self.device = settings.get('microphone_device')

    def transcribe(self, samples, rate):
        import numpy as np
        samples = np.asarray(samples, dtype=np.float32)
        # Do not decode silence: Whisper can invent words from an empty signal.
        if samples.size == 0 or float(np.max(np.abs(samples))) < 0.001:
            return ''
        stream = self.recognizer.create_stream()
        stream.accept_waveform(rate, samples)
        self.recognizer.decode_stream(stream)
        return stream.result.text.strip()

    def listen_once(self):
        import numpy as np
        import sounddevice as sd
        rate = int(sd.query_devices(self.device, 'input')['default_samplerate'])
        audio = queue.Queue(maxsize=100)
        failed = []

        def callback(data, frames, timing, status):
            if status:
                failed.append(str(status))
            try:
                audio.put_nowait(bytes(data))
            except queue.Full:
                failed.append('queue_full')

        input('جاهز — Sherpa-ONNX. اضغط Enter لبدء التسجيل...')
        blocks = []
        frames = 0
        with sd.RawInputStream(samplerate=rate, blocksize=max(800, rate // 5),
                               device=self.device, dtype='int16', channels=1, callback=callback):
            print('● التسجيل شغّال. اضغط Enter للنهاية، أو Ctrl+C للإلغاء.', flush=True)
            while True:
                if msvcrt.kbhit():
                    key = msvcrt.getwch()
                    if key == '\x03':
                        raise KeyboardInterrupt
                    if key == '\r':
                        break
                try:
                    block = audio.get(timeout=0.2)
                except queue.Empty:
                    continue
                blocks.append(block)
                frames += len(block) // 2
                if frames > rate * 120:
                    raise RuntimeError('وصل التسجيل لدقيقتين. جرّب طلبًا أقصر.')
        while not audio.empty():
            blocks.append(audio.get_nowait())
        if failed:
            raise RuntimeError('الصوت اتقطع أثناء التسجيل؛ أعد المحاولة.')
        print('■ انتهى التسجيل. جارٍ التعرف بالعربية عبر ONNX...', flush=True)
        samples = np.frombuffer(b''.join(blocks), dtype=np.int16).astype(np.float32) / 32768.0
        return self.transcribe(samples, rate)
