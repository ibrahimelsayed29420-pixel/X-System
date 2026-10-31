import concurrent.futures
import json
from research_github_components import ROOT, review

EXTRA = {
 'microsoft/agent-framework': 'orchestration',
 'Comfy-Org/ComfyUI': 'image_workflows',
 'FFmpeg/FFmpeg': 'video_processing',
 'remotion-dev/remotion': 'video_generation',
 'docling-project/docling': 'documents',
 'rhasspy/openWakeWord': 'wake_word',
 'langchain-ai/deepagents': 'agent_core',
 'MemTensor/MemOS': 'memory',
}
if __name__ == '__main__':
    path = ROOT / 'evidence.json'
    report = json.loads(path.read_text(encoding='utf-8'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        extra = list(pool.map(review, EXTRA.items()))
    existing = {r['requested_repo'] for r in report['repositories']}
    report['repositories'].extend(r for r in extra if r['requested_repo'] not in existing)
    report['repositories'].sort(key=lambda r:r.get('stargazers_count', -1), reverse=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    for r in extra:
        print(json.dumps({k:r.get(k) for k in ('full_name','stargazers_count','license','error')}, ensure_ascii=False))
