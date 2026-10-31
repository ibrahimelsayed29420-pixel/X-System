import argparse
import json
import sys
from pathlib import Path
from . import brain, hello
from .environment import inspect_environment
from .identity import enroll, load_settings, require_identity
from .speech import ArabicListener, tts


def doctor():
    results = {}
    settings = load_settings()
    results['speech_backend'] = settings.get('speech_backend', 'vosk')
    from .identity import verification_enabled
    results['verification_required'] = verification_enabled()
    reasoning_path = Path(__file__).resolve().parents[1] / 'deep-reasoning.json'
    reasoning = json.loads(reasoning_path.read_text(encoding='utf-8')) if reasoning_path.exists() else {}
    results['mind_engine'] = {'engine': 'Deep Agents' if reasoning.get('enabled') else 'Ollama direct',
                              'model': reasoning.get('model') if reasoning.get('enabled') else settings.get('ollama_model'),
                              'languages': ['Arabic', 'English']}
    probes = {
        'windows_hello': hello.availability,
        'arabic_voices': lambda: [v for v in tts() if v['language'].startswith('ar-')],
        'ollama_models': brain.models,
        'speech_model_present': lambda: all((Path(settings['onnx_model']) / f).is_file() for f in ['base-encoder.int8.onnx','base-decoder.int8.onnx','base-tokens.txt']) if settings.get('speech_backend') == 'sherpa-onnx' else (Path(settings['vosk_model']) / 'am/final.mdl').is_file(),
        'account_enrolled': lambda: bool(load_settings().get('expected_windows_sid')),
    }
    for key, probe in probes.items():
        try:
            results[key] = probe()
        except Exception as exc:
            results[key] = {'error': str(exc)}
    print(json.dumps(results, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description='X — مساعد إبراهيم المحلي التجريبي')
    parser.add_argument('action', choices=['doctor', 'enroll', 'verify', 'inventory', 'devices', 'speak', 'listen', 'chat', 'updates', 'github-status', 'voice-stop', 'research', 'workflow', 'mind-status', 'mind-start', 'mind-open', 'mind-stop'])
    parser.add_argument('--resume', help='Resume a workflow by its saved run ID')
    parser.add_argument('--channel', choices=['web', 'github', 'youtube'], default='web')
    parser.add_argument('--read', action='store_true', help='Read a public URL or repository instead of searching')
    parser.add_argument('--query', help='Public search query or target URL')
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--text', action='store_true', help='Use typed input for chat')
    parser.add_argument('--mute', action='store_true', help='Display the response without generating speech')
    args = parser.parse_args()
    if args.action == 'doctor':
        doctor()
        return
    if args.action == 'enroll':
        enroll()
        return
    # All interactive functions fail closed if enrollment or Hello verification fails.
    if args.action == 'chat':
        settings = load_settings()
        if args.text:
            text = args.query or input('طلبك إلى X: ').strip()
            require_identity()
        else:
            from .identity import verification_enabled
            input('اضغط Enter لبدء التحقق ثم فتح الميكروفون...' if verification_enabled() else 'اضغط Enter لبدء الاستماع...')
            require_identity()
            listener = ArabicListener(settings)
            text = listener.listen_once()
            if not text:
                raise RuntimeError('لم أسمع كلامًا واضحًا.')
            print('سمعت:', text)
            if input('إرسال النص للنموذج المحلي؟ اكتب نعم: ').strip() != 'نعم':
                print('تم الإلغاء.')
                return
            # A fresh verification covers the response after transcription review.
            require_identity()
        reply = brain.answer(text, settings['ollama_model'])
        print('X:', reply)
        if reply and not args.mute:
            tts('speak', reply[:4000])
        return
    require_identity()
    if args.action in ('mind-status','mind-start','mind-open','mind-stop'):
        from .mind_runtime import DATA,ensure_started,status
        if args.action=='mind-start':ensure_started()
        elif args.action=='mind-open':
            import time
            import urllib.error
            import urllib.request
            import webbrowser

            def dashboard_state():
                with urllib.request.urlopen('http://127.0.0.1:18764/api/state',timeout=1) as response:
                    return json.loads(response.read())

            ensure_started()
            url='http://127.0.0.1:18764/'
            for attempt in range(50):
                try:
                    dashboard=dashboard_state()
                    if dashboard.get('chat_available') is True:
                        break
                    runtime=status()
                    pending=DATA/'inbox'
                    has_pending=any(pending.glob('*.json')) if pending.is_dir() else False
                    if runtime.get('state')!='ready' or has_pending:
                        raise RuntimeError('واجهة المحادثة تحتاج تحديثًا، لكن X يعالج طلبًا أو لديه طلب منتظر. أعد فتح الواجهة بعد اكتماله.')
                    DATA.mkdir(parents=True,exist_ok=True)
                    (DATA/'stop.request').write_text('update chat interface',encoding='utf-8')
                    for _ in range(50):
                        if not status().get('process_alive'):
                            break
                        time.sleep(.2)
                    else:
                        raise RuntimeError('تعذر إيقاف واجهة X القديمة بأمان؛ لم يتم إنهاء العملية بالقوة.')
                    ensure_started()
                    for _ in range(50):
                        try:
                            dashboard=dashboard_state()
                            if dashboard.get('chat_available') is True:
                                break
                        except (OSError,urllib.error.URLError):
                            pass
                        time.sleep(.2)
                    else:
                        raise RuntimeError('بدأ عقل X لكن تحديث واجهة المحادثة لم يكتمل.')
                    break
                except (OSError,urllib.error.URLError):
                    if attempt==49:
                        raise RuntimeError('بدأ عقل X لكن واجهة المحادثة لم تصبح جاهزة.')
                    time.sleep(.2)
            if not webbrowser.open_new_tab(url):
                print('افتح هذا الرابط في المتصفح: '+url)
            else:
                print('واجهة X جاهزة: '+url)
        elif args.action=='mind-stop':
            if status().get('process_alive'):
                DATA.mkdir(parents=True,exist_ok=True)
                (DATA/'stop.request').write_text('stop',encoding='utf-8')
        print(json.dumps(status(),ensure_ascii=False,indent=2))
        return
    if args.action == 'workflow':
        from .workflow import run_workflow
        value = '' if args.resume else (args.query or input('مهمة بحث X: ').strip())
        result = run_workflow(value, args.channel, args.limit, args.resume)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get('status') != 'complete':
            raise RuntimeError('المهمة لم تكتمل؛ راجع الخطأ الظاهر')
        return
    if args.action == 'research':
        from .research import research
        value = args.query or input('بحث X — اكتب الطلب أو الرابط: ').strip()
        print(json.dumps(research(args.channel, 'read' if args.read else 'search', value, args.limit), ensure_ascii=False, indent=2))
        return
    if args.action == 'voice-stop':
        from .voicetut_speech import request
        try:
            request('/stop', {}, timeout=5)
            print('تم إيقاف محرك صوت حسن وتحرير ذاكرته.')
        except Exception:
            print('محرك حسن غير متاح أو متوقف بالفعل.')
        return
    if args.action == 'github-status':
        import subprocess
        config = json.loads(Path('D:/X-System/runtime/github-cli/installation.json').read_text())
        result = subprocess.run([config['executable'], 'api', 'user', '--jq', '.login'], capture_output=True, text=True, timeout=30)
        print('GitHub: ' + result.stdout.strip() if result.returncode == 0 else 'افتح Connect-GitHub.cmd وسجّل الدخول أولًا.')
        return
    if args.action == 'updates':
        from .updates import check_updates
        check_updates()
        return
    if args.action == 'verify':
        from .identity import verification_enabled
        print('تم التحقق من حساب إبراهيم عبر Windows Hello.' if verification_enabled() else 'التحقق معطل في نسخة التطوير بطلب إبراهيم.')
    elif args.action == 'inventory':
        print(json.dumps(inspect_environment(), ensure_ascii=False, indent=2))
    elif args.action == 'devices':
        import sounddevice as sd
        print(sd.query_devices())
    elif args.action == 'speak':
        tts('speak', 'أهلًا يا إبراهيم، أنا إكس. الصوت العربي المحلي جاهز للتجربة.')
    elif args.action == 'listen':
        print('النص:', ArabicListener(load_settings()).listen_once())


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        main()
    except KeyboardInterrupt:
        print('\nتم الإيقاف وإغلاق الاستماع.')
        sys.exit(130)
    except Exception as exc:
        print('X:', str(exc), file=sys.stderr)
        sys.exit(1)
