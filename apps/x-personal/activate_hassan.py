import json
from pathlib import Path

root=Path(__file__).resolve().parent
report=json.loads((root/'hassan-verification.json').read_text(encoding='utf-8'))
if report.get('status')!='PASS' or report.get('speaker')!='Hassan':
    raise RuntimeError('A successful local Hassan test is required')
settings_path=root/'settings.json'
settings=json.loads(settings_path.read_text(encoding='utf-8'))
backup=root/'settings.before-hassan.json'
if not backup.exists():backup.write_text(json.dumps(settings,ensure_ascii=False,indent=2),encoding='utf-8')
settings['tts_backend']='voicetut'
settings['preferred_voice']={'engine':'voicetut','speaker':'Hassan','status':'active'}
settings_path.write_text(json.dumps(settings,ensure_ascii=False,indent=2),encoding='utf-8')
print('Hassan activated; previous settings saved.')
