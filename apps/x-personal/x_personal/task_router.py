"""Deterministic routing between X's local dialogue and specialist agents."""
import re
from .real_estate import is_listing_request

_RESEARCH = re.compile(
    r'\b(?:search|look up|find|research)\b|ابحث|دور(?:لي)?|بحث',
    re.IGNORECASE,
)
_COMPLEX = re.compile(
    r'\b(?:analy[sz]e|compare|plan|design|build|implement|evaluate|'
    r'multi[- ]step|workflow|strategy)\b|حلل|قارن|خطط|خطة|صمم|نفذ|'
    r'خطوات|استراتيجية|workflow',
    re.IGNORECASE,
)
_PLANNING = re.compile(
    r'\b(?:plan|roadmap|steps|step by step|break down)\b|خطة|خطط|خطوات|رتب(?:لي)?',
    re.IGNORECASE,
)
_REAL_ESTATE = re.compile(
    r'\b(?:real estate|property|properties|rental|rent|listing|off[- ]plan|'
    r'villa|apartment|land|brokerage)\b|عقار|عقارات|إيجار|تأجير|بيع|أرض|أراضي|'
    r'أوف\s*بلان|شقة|فيلا|عقار|إعلان عقاري|عرض عقاري',
    re.IGNORECASE,
)


def route_request(text, dialogue_model, agent_model, agents_enabled=True):
    """Choose one local route without calling a model or exposing new tools."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError('اكتب طلبًا غير فارغ لتحديد المسار.')

    if _RESEARCH.search(text):
        return {
            'agent': 'research-specialist',
            'skill': 'research',
            'model': agent_model if agents_enabled else dialogue_model,
            'reason': 'request needs current public sources',
        }

    if is_listing_request(text) and _REAL_ESTATE.search(text):
        return {
            'agent': 'real-estate-specialist',
            'skill': 'real_estate',
            'model': 'local-template',
            'reason': 'listing drafts use a fact-preserving local template',
        }

    if not agents_enabled:
        return {
            'agent': 'dialogue',
            'skill': 'dialogue',
            'model': dialogue_model,
            'reason': 'specialist agents are disabled',
        }

    if _REAL_ESTATE.search(text):
        return {
            'agent': 'real-estate-specialist',
            'skill': 'real_estate',
            'model': agent_model,
            'reason': 'request concerns real estate work',
        }

    if _PLANNING.search(text):
        return {
            'agent': 'workflow-planner',
            'skill': 'planning',
            'model': agent_model,
            'reason': 'request explicitly asks for a plan or steps',
        }

    sentences = len(re.findall(r'[.!?؟]+', text))
    if _COMPLEX.search(text) or len(text) > 180 or sentences > 2:
        return {
            'agent': 'workflow-orchestrator',
            'skill': 'planning',
            'model': agent_model,
            'reason': 'request has multi-step or analytical signals',
        }

    return {
        'agent': 'dialogue',
        'skill': 'dialogue',
        'model': dialogue_model,
        'reason': 'short single-turn conversation',
    }
