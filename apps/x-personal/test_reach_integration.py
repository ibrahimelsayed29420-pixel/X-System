import concurrent.futures
import datetime
import json
from pathlib import Path
from x_personal.research import research

CASES = [
    ('github', 'read', 'Panniantong/Agent-Reach'),
    ('web', 'read', 'https://example.com'),
    ('web', 'search', 'Ajman real estate market official'),
    ('youtube', 'read', 'https://www.youtube.com/watch?v=jNQXAC9IVRw'),
    ('web', 'read', 'http://127.0.0.1:11434'),
]

def check(case):
    try:
        result = research(*case, limit=2)
        items = result.get('items', [])
        return {'channel': case[0], 'action': case[1], 'target': case[2],
                'ok': result.get('ok'), 'item_count': len(items),
                'source_urls': [item.get('url') for item in items],
                'error': result.get('error')}
    except Exception as exc:
        return {'channel': case[0], 'target': case[2], 'ok': False, 'error': str(exc)}

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(check, CASES))
    report = {'tested_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'results': results}
    Path(__file__).with_name('reach-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
