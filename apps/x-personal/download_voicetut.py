import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

codec='--codec' in sys.argv
repo='eustlb/higgs-audio-v2-tokenizer' if codec else 'mohammedaly22/VoiceTut-TTS'
with urllib.request.urlopen('https://huggingface.co/api/models/'+repo+'?blobs=true',timeout=30) as response:
    info=json.load(response)
root=Path('D:/X-System/models/tts/voicetut/audio_tokenizer' if codec else 'D:/X-System/models/tts/voicetut')
root.mkdir(parents=True,exist_ok=True)
def download(item):
    name=item['rfilename']
    if name.startswith('.') or name=='README.md':return
    target=root/name
    target.parent.mkdir(parents=True,exist_ok=True)
    partial=target.with_name(target.name+'.part')
    if not target.exists() or target.stat().st_size!=item['size']:
        url='https://huggingface.co/'+repo+'/resolve/'+info['sha']+'/'+name
        if item['size'] > 500*1024*1024:
            prefix=partial.stat().st_size if partial.exists() else 0
            if prefix>item['size']:raise RuntimeError('Oversized partial file')
            chunk=(item['size']-prefix+7)//8
            bounds=[(i,start,min(start+chunk,item['size'])-1) for i,start in enumerate(range(prefix,item['size'],max(1,chunk)))]
            def get_range(bound):
                i,start,end=bound
                piece=partial.with_name(partial.name+f'.range{i}')
                size=end-start+1
                if not piece.exists() or piece.stat().st_size!=size:
                    subprocess.run(['curl.exe','-L','--fail','--silent','--show-error','--retry','3','--max-time','1800',
                        '--range',f'{start}-{end}','--max-filesize',str(size),'--output',str(piece),url],check=True)
                if piece.stat().st_size!=size:raise RuntimeError('Incomplete model range')
                print(f'Model range {i+1} ready',flush=True)
                return piece
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as workers:
                pieces=list(workers.map(get_range,bounds))
            with partial.open('ab') as output:
                for piece in pieces:
                    with piece.open('rb') as source:
                        while block:=source.read(1024*1024):output.write(block)
            for piece in pieces:piece.unlink()
        else:
            subprocess.run(['curl.exe','-L','--fail','--silent','--show-error','--retry','3','--max-time','1800','--output',str(partial),url],check=True)
        if partial.stat().st_size!=item['size']:raise RuntimeError('Size mismatch: '+name)
        partial.replace(target)
    expected=item.get('lfs',{}).get('sha256')
    if expected:
        with target.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=expected:raise RuntimeError('Hash mismatch: '+name)
    print('Verified '+name,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(download,info['siblings']))
(root/'x-source.json').write_text(json.dumps({'repo':repo,'revision':info['sha']},indent=2),encoding='utf-8')
print('VoiceTut snapshot ready',flush=True)
