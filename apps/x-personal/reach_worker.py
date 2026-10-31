"""X's bounded adapter to pinned Agent-Reach public research backends."""
import json
import os
import sys
from pathlib import Path

for key in ('GH_TOKEN', 'GITHUB_TOKEN', 'OPENAI_API_KEY', 'GROQ_API_KEY'):
    os.environ.pop(key, None)

def execute(channel, action, value, limit=5):
    from agent_reach.config import Config
    from agent_reach.channels.github import GitHubChannel
    from agent_reach.channels.web import WebChannel
    from agent_reach.channels.youtube import YouTubeChannel
    # Use a separate, empty configuration; never import browser sessions.
    Config.CONFIG_DIR = Path('D:/X-System/data/agent-reach-public')
    Config.CONFIG_FILE = Config.CONFIG_DIR / 'config.yaml'
    routes = {
        ('web', 'search'): (WebChannel(), '_exa_search'),
        ('web', 'read'): (WebChannel(), '_jina_read'),
        ('github', 'search'): (GitHubChannel(), '_api_search'),
        ('github', 'read'): (GitHubChannel(), '_api_read'),
        ('youtube', 'search'): (YouTubeChannel(), '_ytdlp_search'),
        ('youtube', 'read'): (YouTubeChannel(), '_ytdlp_read'),
    }
    if (channel, action) not in routes:
        raise ValueError('Unsupported research channel/action')
    if not value.strip() or len(value) > 2000 or not 1 <= limit <= 10:
        raise ValueError('Invalid query or limit')
    instance, method = routes[channel, action]
    kwargs = {'query': value, 'limit': limit} if action == 'search' else {'target': value}
    items = getattr(instance, method)(**kwargs, timeout=30)
    return {'ok': True, 'channel': channel, 'action': action,
            'backend': method.lstrip('_'), 'items': items,
            'source_trust': 'external_untrusted_content', 'account_access': False}

if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        request = json.loads(sys.stdin.read(12000))
        result = execute(**request)
    except Exception as exc:
        result = {'ok': False, 'error': {'code': getattr(exc, 'code', type(exc).__name__),
                                        'message': str(exc)[:500]}}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result['ok'] else 1)
