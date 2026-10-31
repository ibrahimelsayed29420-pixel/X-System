import datetime
import json
from pathlib import Path
import shutil
import tomllib

config=Path.home()/'.codex/config.toml'
text=config.read_text(encoding='utf-8-sig')
old=tomllib.loads(text)
name='playwright-x'
if name in old.get('mcp_servers',{}):raise RuntimeError('Existing server requires review before replacement')
entry='D:/X-System/runtime/playwright-mcp/node_modules/@playwright/mcp/cli.js'
node='C:/Users/nenoh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
text+='\n[mcp_servers.'+name+']\ncommand = '+json.dumps(node)+'\nargs = '+json.dumps([entry,'--browser','msedge','--isolated','--headless'])+'\nstartup_timeout_sec = 60\ntool_timeout_sec = 60\n'
tomllib.loads(text)
backup=config.with_name('config.before-playwright-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.toml')
shutil.copy2(config,backup)
config.write_text(text,encoding='utf-8')
print('PASS: Playwright registered; existing connections preserved; settings backup saved.')
