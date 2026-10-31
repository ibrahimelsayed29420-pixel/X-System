"""Create X's Ollama persona from existing weights, then select it locally."""
import json
from pathlib import Path
import shutil
from x_personal.brain import local_request, models, system_prompt

ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    base='llama3.2:latest'
    if base not in models():raise RuntimeError('Base local model is missing')
    result=local_request('/api/create',{
        'model':'x-ibrahim:latest','from':base,'stream':False,
        'system':system_prompt(),
        'parameters':{'temperature':0.3,'num_ctx':8192,'num_predict':240}},timeout=120)
    if result.get('status')!='success' or 'x-ibrahim:latest' not in models():
        raise RuntimeError('X model creation did not succeed')
    settings=ROOT/'settings.json'
    backup=ROOT/'settings.before-mind.json'
    if not backup.exists():shutil.copy2(settings,backup)
    config=json.loads(settings.read_text(encoding='utf-8-sig'))
    config['ollama_model']='x-ibrahim:latest'
    temporary=settings.with_suffix('.tmp')
    temporary.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    temporary.replace(settings)
    (ROOT/'mind-installation.json').write_text(json.dumps({
        'model':'x-ibrahim:latest','base_model':base,'weights_trained':False,
        'engine':'LangGraph','memory':'D:/X-System/data/mind/memory.sqlite',
        'identity_verification':'disabled_during_development_by_user',
        'dashboard_listener':'127.0.0.1:18764 read-only',
        'background_runtime':'per-user Windows startup',
        'semantic_memory':'Mem0 OSS + Qdrant local + Ollama BGE-M3'},ensure_ascii=False,indent=2),encoding='utf-8')
    print('X persona created from existing local weights; configuration selected.')
