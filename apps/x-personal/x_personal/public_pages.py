"""Validation and the isolated public-page reading capability."""
import ipaddress
import json
from pathlib import Path
import socket
import subprocess
from urllib.parse import urlsplit,urlunsplit,parse_qsl

ROOT=Path(__file__).resolve().parents[1]

def public_url(value):
    if not isinstance(value,str) or not 1<=len(value)<=2000:
        raise ValueError('Invalid public URL')
    parsed=urlsplit(value.strip())
    if parsed.scheme not in ('https','http') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Only public HTTP(S) URLs without credentials are supported')
    if parsed.port not in (None,80,443):raise ValueError('Only standard web ports are supported')
    if any(any(s in key.lower() for s in ('token','password','secret','session','scrumb')) for key,_ in parse_qsl(parsed.query)):
        raise ValueError('Session or credential links are not public research URLs')
    addresses=socket.getaddrinfo(parsed.hostname,parsed.port or (443 if parsed.scheme=='https' else 80),type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError('Private, local and reserved network addresses are not allowed')
    return urlunsplit((parsed.scheme,parsed.netloc,parsed.path or '/',parsed.query,''))

def read_public_page(url):
    target=public_url(url)
    try:
        process=subprocess.run(['D:/X-System/runtime/crawl4ai-venv/Scripts/python.exe',str(ROOT/'crawl_worker.py')],
            input=json.dumps({'url':target}),capture_output=True,text=True,encoding='utf-8',timeout=65)
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError('تجاوز قارئ الصفحات مهلة 65 ثانية') from exc
    try:return json.loads(process.stdout)
    except ValueError:raise RuntimeError('Page reader returned no valid result') from None
