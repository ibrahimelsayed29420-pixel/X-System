import json
import urllib.request
from x_personal.brain import models

if 'bge-m3:latest' in models():
    print('Embedding model already available')
else:
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req=urllib.request.Request('http://127.0.0.1:11434/api/pull',
        data=json.dumps({'model':'bge-m3:latest','stream':True}).encode(),headers={'Content-Type':'application/json'})
    previous=-1
    with opener.open(req,timeout=600) as response:
        for line in response:
            event=json.loads(line)
            if event.get('error'):raise RuntimeError(event['error'])
            total=event.get('total',0)
            percent=int(event.get('completed',0)*100/total) if total else 0
            if percent//10!=previous:
                print(event.get('status'),percent,flush=True);previous=percent//10
    if 'bge-m3:latest' not in models():raise RuntimeError('Embedding model unavailable after download')
    print('Embedding model downloaded and verified by Ollama')
