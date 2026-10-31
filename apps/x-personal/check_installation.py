"""Noninteractive checks: no microphone stream, Hello prompt or camera use."""
import base64
import json
from pathlib import Path
import platform
import subprocess
import sys
import sysconfig
from x_personal import brain, hello
from x_personal.identity import load_settings
from x_personal.speech import tts

root = Path(__file__).resolve().parent
report = {'python': platform.python_version(), 'python_build_platform': sysconfig.get_platform(),
          'microphone_opened': False, 'camera_opened': False,
          'hello_verification_by_user': 'NOT_TESTED', 'account_enrolled': False}
report['hello_availability'] = hello.availability()
runtime = hello.Runtime()
factory = None
try:
    factory = runtime.factory('39e050c3-4e74-441a-8dc0-b81104df949c')
    report['desktop_hello_factory'] = 'PASS'
finally:
    hello.release(factory)
    runtime.close()
render = tts('render', 'أهلًا يا إبراهيم، أنا إكس.')
wav = base64.b64decode(render['wav_b64'])
assert wav[:4] == b'RIFF' and len(wav) > 1000
report['tts'] = {'status': 'PASS', 'voice': render['voice'], 'language': render['language'], 'wav_bytes': len(wav), 'played': False}
report['ollama_models'] = brain.models()
import sounddevice as sd
report['microphone_device_count'] = sum(d['max_input_channels'] > 0 for d in sd.query_devices())
settings = load_settings()
report['account_enrolled'] = bool(settings.get('expected_windows_sid'))
model_path = Path(settings['vosk_model'])
report['speech_model'] = {'present': (model_path / 'am/final.mdl').is_file(), 'transcription': 'NOT_TESTED_WITH_HUMAN_SPEECH'}
if report['speech_model']['present']:
    from vosk import Model, KaldiRecognizer, SetLogLevel
    SetLogLevel(-1)
    model = Model(str(model_path))
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.AcceptWaveform(bytes(32000))
    assert not json.loads(recognizer.FinalResult()).get('text')
    report['speech_model']['load_and_silence_test'] = 'PASS'
tests_dir = root / 'tests'
crawler_python = root.parents[1] / 'runtime' / 'crawl4ai-venv' / 'Scripts' / 'python.exe'
workflow_python = root.parents[1] / 'runtime' / 'x-workflow-venv' / 'Scripts' / 'python.exe'
test_failures = []
for test_file in sorted(tests_dir.glob('test_*.py')):
    test_python = (
        crawler_python if test_file.name == 'test_crawl_worker.py'
        else workflow_python if test_file.name == 'test_mind_worker_routing.py'
        else Path(sys.executable)
    )
    if not test_python.is_file():
        raise FileNotFoundError(f'Required test interpreter not found: {test_python}')
    test = subprocess.run(
        [str(test_python), '-m', 'unittest', 'discover', '-s', 'tests', '-p', test_file.name],
        cwd=root, capture_output=True, text=True,
    )
    if test.returncode:
        test_failures.append(f'{test_file.name}\n{test.stdout}{test.stderr}')
report['boundary_tests'] = 'PASS' if not test_failures else 'FAIL'
if test_failures:
    raise RuntimeError('\n'.join(test_failures))
path = root / 'verification.json'
path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
