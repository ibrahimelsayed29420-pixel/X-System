"""Collect public GitHub evidence; never install or execute reviewed projects."""
import concurrent.futures
import datetime as dt
import json
from pathlib import Path
import urllib.request

REPOS = {
 'openclaw/openclaw': 'agent_core',
 'NousResearch/hermes-agent': 'agent_core',
 'langchain-ai/langgraph': 'orchestration',
 'microsoft/autogen': 'orchestration',
 'crewAIInc/crewAI': 'orchestration',
 'mem0ai/mem0': 'memory',
 'letta-ai/letta': 'memory',
 'qdrant/qdrant': 'memory_storage',
 'chroma-core/chroma': 'memory_storage',
 'Panniantong/Agent-Reach': 'research',
 'unclecode/crawl4ai': 'research',
 'firecrawl/firecrawl': 'research',
 'browser-use/browser-use': 'browser',
 'microsoft/playwright-mcp': 'browser',
 'activepieces/activepieces': 'automation',
 'n8n-io/n8n': 'automation',
 'gitroomhq/postiz-app': 'social_content',
 'chatwoot/chatwoot': 'inbox',
 'frappe/crm': 'crm',
 'twentyhq/twenty': 'crm',
 'Sapheron/AgenticCRM': 'crm',
 'SYSTRAN/faster-whisper': 'speech_recognition',
 'k2-fsa/sherpa-onnx': 'speech_onnx',
 'snakers4/silero-vad': 'speech_activity',
 'OHF-Voice/piper1-gpl': 'speech_synthesis',
 'MohammedAly22/VoiceTuT-TTS': 'speech_synthesis',
 'k2-fsa/OmniVoice': 'speech_synthesis',
 'odysseus-dev/odysseus': 'workspace',
}
ROOT = Path(__file__).resolve().parent / 'research' / 'github-components-2026-10-30'

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'X-component-review', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read(2_000_000)

def review(pair):
    repo, category = pair
    result = {'requested_repo': repo, 'category': category}
    try:
        data = json.loads(fetch('https://api.github.com/repos/' + repo))
        result.update({key: data.get(key) for key in ('full_name', 'html_url', 'description', 'stargazers_count', 'forks_count', 'pushed_at', 'archived', 'default_branch', 'open_issues_count')})
        result['license'] = (data.get('license') or {}).get('spdx_id')
        result['readme_url'] = f"https://raw.githubusercontent.com/{data['full_name']}/{data['default_branch']}/README.md"
        try:
            readme = fetch(result['readme_url']).decode('utf-8', errors='replace')
            (ROOT / (repo.replace('/', '__') + '.README.md')).write_text(readme, encoding='utf-8')
            result['readme_saved'] = True
        except Exception as exc:
            result['readme_error'] = str(exc)
    except Exception as exc:
        result['error'] = str(exc)
    return result

if __name__ == '__main__':
    ROOT.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(review, REPOS.items()))
    results.sort(key=lambda r: r.get('stargazers_count', -1), reverse=True)
    report = {'observed_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'method': 'Public GitHub REST metadata + upstream README; star order within reviewed candidates, not an exhaustive global ranking', 'repositories': results}
    (ROOT / 'evidence.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    for r in results:
        print(json.dumps({key:r.get(key) for key in ('full_name','category','stargazers_count','license','pushed_at','archived','error')}, ensure_ascii=False))
