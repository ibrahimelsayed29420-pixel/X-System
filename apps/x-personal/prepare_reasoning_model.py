import json
import urllib.request
from x_personal.brain import models

MODEL='qwen3:4b-instruct'
if MODEL in models():
    print('Reasoning model already available')
else:
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req=urllib.request.Request('http://127.0.0.1:11434/api/pull',
        data=json.dumps({'model':MODEL,'stream':True}).encode(),headers={'Content-Type':'application/json'})
    previous={}
    with opener.open(req,timeout=600) as response:
        for line in response:
            event=json.loads(line)
            if event.get('error'):raise RuntimeError(event['error'])
            total=event.get('total',0);digest=event.get('digest','manifest')
            percent=int(event.get('completed',0)*100/total) if total else 0
            if previous.get(digest)!=percent//10:
                print(event.get('status'),percent,flush=True);previous[digest]=percent//10
    if MODEL not in models():raise RuntimeError('Reasoning model unavailable after download')
    print('Reasoning model downloaded and verified by Ollama')
