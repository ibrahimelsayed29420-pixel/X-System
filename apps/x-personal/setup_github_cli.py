import io
import json
from pathlib import Path
import urllib.request
import zipfile

root=Path('D:/X-System/runtime/github-cli')
request=urllib.request.Request('https://api.github.com/repos/cli/cli/releases/latest',headers={'User-Agent':'X-setup'})
with urllib.request.urlopen(request,timeout=30) as response:
    release=json.load(response)
asset=next(a for a in release['assets'] if a['name'].endswith('windows_arm64.zip'))
with urllib.request.urlopen(asset['browser_download_url'],timeout=60) as response:
    archive=response.read(60*1024*1024)
root.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(io.BytesIO(archive)) as zf:
    if zf.testzip():raise RuntimeError('Archive CRC failed')
    for info in zf.infolist():
        name=info.filename.replace('\\','/')
        if '..' in Path(name).parts or ':' in name or name.startswith('/'):
            raise RuntimeError('Unsafe archive path')
    zf.extractall(root)
exe=list(root.rglob('gh.exe'))
if len(exe)!=1:raise RuntimeError('GitHub CLI executable is ambiguous')
config={'version':release['tag_name'],'executable':str(exe[0]),'source':asset['browser_download_url']}
(root/'installation.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
launcher=Path(__file__).with_name('Connect-GitHub.cmd')
launcher.write_text('@echo off\r\n"'+str(exe[0])+'" auth login --hostname github.com --web --git-protocol https --skip-ssh-key\r\npause\r\n',encoding='ascii')
print(json.dumps({'version':release['tag_name'],'launcher':str(launcher)}))
