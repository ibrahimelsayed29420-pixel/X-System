"""Mem0 OSS + local Qdrant + Ollama BGE-M3. Network restricted to loopback."""
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import sys

DATA=Path('D:/X-System/data/mind/semantic')
os.environ['MEM0_TELEMETRY']='false'
os.environ['MEM0_DIR']=str(DATA/'config')
for key in ('OPENAI_API_KEY','MEM0_API_KEY','GROQ_API_KEY','ANTHROPIC_API_KEY'):
    os.environ.pop(key,None)

def network_boundary(event,args):
    if event=='socket.connect':
        address=args[1]
        if isinstance(address,tuple):
            try:allowed=ipaddress.ip_address(address[0]).is_loopback
            except ValueError:allowed=False
            if not allowed:raise PermissionError('Semantic memory only connects to loopback')

sys.addaudithook(network_boundary)

def execute(query, facts, data_dir=None):
    target=Path(data_dir or DATA);target.mkdir(parents=True,exist_ok=True)
    from x_personal.brain import models
    if 'bge-m3:latest' not in models():raise RuntimeError('Local BGE-M3 model is missing; no automatic download')
    from mem0 import Memory
    engine=Memory.from_config({
        'llm':{'provider':'ollama','config':{'model':'x-ibrahim:latest','ollama_base_url':'http://127.0.0.1:11434'}},
        'embedder':{'provider':'ollama','config':{'model':'bge-m3:latest','embedding_dims':1024,'ollama_base_url':'http://127.0.0.1:11434'}},
        'vector_store':{'provider':'qdrant','config':{'collection_name':'x_facts','path':str(target/'qdrant'),'embedding_model_dims':1024,'on_disk':True}},
        'history_db_path':str(target/'history.sqlite'),
    })
    mapping_path=target/'mapping.json'
    mapping=json.loads(mapping_path.read_text(encoding='utf-8')) if mapping_path.exists() else {}
    current={str(row['id']):row['content'] for row in facts}
    def save_map():
        temporary=mapping_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(mapping,ensure_ascii=False),encoding='utf-8');temporary.replace(mapping_path)
    for key in list(mapping):
        digest=hashlib.sha256(current.get(key,'').encode()).hexdigest()
        if key not in current or digest!=mapping[key]['hash']:
            for memory_id in mapping[key]['ids']:engine.delete(memory_id)
            del mapping[key];save_map()
    for key,content in current.items():
        if key in mapping:continue
        added=engine.add(content,user_id='ibrahim',infer=False,metadata={'source':'explicit_user_memory','fact_id':key})
        ids=[r['id'] for r in added.get('results',[]) if r.get('id')]
        if not ids:raise RuntimeError('Mem0 did not return stored memory IDs')
        mapping[key]={'ids':ids,'hash':hashlib.sha256(content.encode()).hexdigest()};save_map()
    result=engine.search(query,top_k=4,filters={'user_id':'ibrahim'},threshold=.1,rerank=False) if current else {'results':[]}
    return {'ok':True,'items':[{'content':row.get('memory'), 'score':row.get('score'),
             'fact_id':(row.get('metadata') or {}).get('fact_id')} for row in result.get('results',[])],
             'local_only':True,'indexed_facts':len(mapping)}

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    try:
        args=json.loads(sys.stdin.read(60000));result=execute(**args)
    except Exception as exc:result={'ok':False,'error':str(exc)[:500]}
    print(json.dumps(result,ensure_ascii=False));sys.exit(0 if result.get('ok') else 1)
