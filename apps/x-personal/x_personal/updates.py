"""Read public release metadata only. Never install or execute downloaded code."""
import datetime
import json
from pathlib import Path
import urllib.request

PROJECTS = ['OHF-Voice/piper1-gpl', 'k2-fsa/sherpa-onnx', 'snakers4/silero-vad']


def check_updates():
    results = []
    for repo in PROJECTS:
        request = urllib.request.Request('https://api.github.com/repos/'+repo+'/releases/latest',
            headers={'User-Agent':'X-release-review','Accept':'application/vnd.github+json'})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                release = json.load(response)
            results.append({'repository':repo,'latest_tag':release['tag_name'],
                            'published_at':release.get('published_at'),'url':release['html_url'],
                            'action':'Review compatibility and tests before upgrading'})
        except Exception as exc:
            results.append({'repository':repo,'error':str(exc)})
    report = {'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'mode':'public-read-only','account_authentication':False,
              'automatic_install':False,'projects':results}
    output = Path('D:/X-System/logs/x-release-review.json')
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
