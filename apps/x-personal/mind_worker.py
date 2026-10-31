"""X mind: recall -> explicit intent -> bounded public search -> reply -> save."""
import json
import re
import sys
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from x_personal import brain, memory
from x_personal import skill_graph
from x_personal import semantic_memory
from x_personal import deep_reasoning
from x_personal import task_router
from x_personal.research import research

class MindState(TypedDict,total=False):
    text:str
    model:str
    session:str
    history:list
    facts:list
    intent:str
    query:str
    evidence:dict
    reply:str
    agent_tools:list
    route:dict

def recall(state):
    facts=memory.facts()
    command=state['text'].strip()
    if facts and command.casefold() not in ('ذاكرتك','الذاكرة','اعرض الذاكرة','/memory','your memory','show memory','show memories') and not command.casefold().startswith(('احفظ ','افتكر ','اتعلم ','انس ','امسح من الذاكرة ','remember ','learn ','forget ','delete memory ')):
        semantic=semantic_memory.retrieve(command,facts)
        if semantic.get('ok') and semantic.get('items'):
            ids={str(row.get('fact_id')) for row in semantic['items']}
            facts=[row for row in facts if str(row['id']) in ids] or facts
    return {'history':memory.history(state['session']),'facts':facts}

def intent(state):
    text=state['text'].strip()
    lowered=text.casefold()
    if re.search(r'\b(?:who are you|your name|what are you called)\b',lowered):
        return {'intent':'direct','reply':"I'm X, your digital assistant, Ibrahim."}
    if lowered in ('your memory','show memory','show memories','/memory'):
        return {'intent':'direct','reply':'\n'.join(f"{row['id']}. {row['content']}" for row in state['facts']) or 'No explicitly saved memories yet.'}
    if lowered.startswith(('remember ','learn ')):
        prefix='remember ' if lowered.startswith('remember ') else 'learn '
        content=text[len(prefix):].strip()
        if prefix=='learn ':skill_graph.learn(content)
        memory.remember(content)
        return {'intent':'direct','reply':'Saved locally.' if prefix=='remember ' else 'Saved this lesson and linked it to related skills.'}
    english_forget=re.fullmatch(r'(?:forget|delete memory)\s+(\d+)',lowered)
    if english_forget:
        number=int(english_forget[1])
        for row in state['facts']:
            if row['id']==number:skill_graph.forget_lesson(row['content'])
        removed=memory.forget(number)
        return {'intent':'direct','reply':'Removed that saved memory.' if removed else 'That memory ID was not found.'}
    if re.search(r'(?:اسمك|إنت مين|انت مين|أنت مين|من أنت|من انت)',text):
        return {'intent':'direct','reply':'أنا إكس، مساعدك الرقمي يا إبراهيم. إنت إبراهيم وأنا X.'}
    if text.startswith('اتعلم '):
        content=text[len('اتعلم '):].strip()
        skill_graph.learn(content)
        memory.remember(content)
        return {'intent':'direct','reply':'حفظت الخبرة وربطتها بالمهارات المرتبطة بكلامك.'}
    if text in ('مهاراتك','خريطة المهارات'):
        graph=skill_graph.snapshot()
        return {'intent':'direct','reply':'المهارات والخبرات المترابطة:\n'+'\n'.join(s['title'] for s in graph['skills'])}
    if text.startswith(('احفظ ','افتكر إن ','افتكر ان ')):
        prefix=next(p for p in ('احفظ ','افتكر إن ','افتكر ان ') if text.startswith(p))
        memory.remember(text[len(prefix):])
        return {'intent':'direct','reply':'حفظتها عندي يا إبراهيم.'}
    if text in ('ذاكرتك','الذاكرة','اعرض الذاكرة','/memory'):
        rows=state['facts']
        return {'intent':'direct','reply':'\n'.join(f"{row['id']}. {row['content']}" for row in rows) or 'لسه مفيش معلومات محفوظة بطلبك. ملف شغلك الأساسي موجود.'}
    match=re.fullmatch(r'(?:انس|امسح من الذاكرة)\s+(\d+)',text)
    if match:
        for row in state['facts']:
            if row['id']==int(match[1]):skill_graph.forget_lesson(row['content'])
        removed=memory.forget(int(match[1]))
        return {'intent':'direct','reply':'مسحت المعلومة المحفوظة.' if removed else 'رقم المعلومة ده مش موجود.'}
    match=re.match(r'^(?:ابحث(?: عن)?|دور(?:لي)?(?: على| علي)?|بحث|search(?: for)?|look up|find)\s+(.+)',text,re.S|re.I)
    if match:
        return {'intent':'search','query':match[1][:2000]}
    return {'intent':'chat'}

def search(state):
    result=research('web','search',state['query'],3)
    evidence={'ok':result.get('ok'), 'error':result.get('error'), 'items':[
        {'title':i.get('title'),'url':i.get('url'),'text':str(i.get('text') or '')[:900]}
        for i in result.get('items',[])[:3]]}
    return {'evidence':evidence}

def respond(state):
    if state.get('reply'):
        return {}
    route=task_router.route_request(
        state['text'],
        dialogue_model=state['model'],
        agent_model=deep_reasoning.model(),
        agents_enabled=deep_reasoning.enabled(),
    )
    state['route']=route
    if route['agent']=='research-specialist':
        evidence=state.get('evidence')
        if evidence is None:
            raise RuntimeError('لم يُنفذ البحث المطلوب؛ لا توجد مصادر للتحقق.')
        if not evidence.get('ok'):
            return {'reply':'البحث متاح بس المحاولة دي ما نجحتش. مش هخمن نتائج؛ جرّب تاني بعد شوية.','route':route}
        if not brain.gemini_api_key() and route['model'] not in brain.models():
            raise RuntimeError(f"النموذج المحلي المحدد غير مثبت: {route['model']}")
        reply=brain.generate(state['text'],route['model'],state['history'],state['facts'],
                             evidence,route=route)
        if not reply:
            raise RuntimeError('النموذج المحلي رجع ردًا فارغًا')
        urls=list(dict.fromkeys(
            item.get('url') for item in evidence.get('items',[])
            if isinstance(item.get('url'),str) and item['url'].startswith(('https://','http://'))
        ))
        if urls:
            reply+='\n\nمصادر البحث:\n'+'\n'.join(urls)
        return {'reply':reply,'route':route,'agent_tools':[{'name':'research-specialist','state':'complete'}]}
    if route['agent']=='real-estate-specialist':
        from x_personal.real_estate import build_listing_draft,is_listing_request
        if is_listing_request(state['text']):
            reply=build_listing_draft(state['text'])
            return {'reply':reply,'route':route,
                    'agent_tools':[{'name':'real-estate-specialist','state':'complete'}]}
        if not brain.gemini_api_key() and route['model'] not in brain.models():
            raise RuntimeError(f"النموذج المحلي المحدد غير مثبت: {route['model']}")
        reply=brain.generate(state['text'],route['model'],state['history'],state['facts'],
                             state.get('evidence'),specialty='real_estate',route=route)
        if not reply:
            raise RuntimeError('مساعد العقارات المحلي رجع ردًا فارغًا')
        return {'reply':reply,'route':route,
                'agent_tools':[{'name':'real-estate-specialist','state':'complete'}]}
    if route['agent'] in ('workflow-planner','workflow-orchestrator'):
        output=deep_reasoning.respond(state,route)
        return {'reply':output['reply'],'agent_tools':output.get('tools',[]),'route':route}
    evidence=state.get('evidence')
    if evidence is not None and not evidence.get('ok'):
        return {'reply':'البحث متاح بس المحاولة دي ما نجحتش. مش هخمن نتائج؛ جرّب تاني بعد شوية.'}
    if not brain.gemini_api_key() and route['model'] not in brain.models():
        raise RuntimeError(f"النموذج المحلي المحدد غير مثبت: {route['model']}")
    reply=brain.generate(state['text'],route['model'],state['history'],state['facts'],
                         evidence,route=route)
    if not reply:
        raise RuntimeError('النموذج المحلي رجع ردًا فارغًا')
    urls=[]
    for item in (evidence or {}).get('items',[]):
        url=item.get('url') or ''
        if url.startswith(('https://','http://')) and url not in urls:
            urls.append(url)
    if urls:
        reply+='\n\nمصادر البحث:\n'+'\n'.join(urls)
    return {'reply':reply,'route':route}

def save(state):
    memory.append_pair(state['session'],state['text'],state['reply'])
    return {}

def observe_node(name,node):
    def wrapped(state):
        import datetime as dt
        from pathlib import Path
        folder=Path('D:/X-System/data/mind/runtime');folder.mkdir(parents=True,exist_ok=True)
        def emit(status):
            record={'stage':name,'state':status,'at':dt.datetime.now(dt.timezone.utc).isoformat()}
            temporary=folder/'stage.tmp'
            temporary.write_text(json.dumps(record),encoding='utf-8')
            import time
            for attempt in range(20):
                try:
                    temporary.replace(folder/'stage.json')
                    break
                except PermissionError:
                    if attempt==19:raise
                    time.sleep(.025)
            with (folder/'events.jsonl').open('a',encoding='utf-8') as handle:handle.write(json.dumps(record)+'\n')
        emit('running')
        try:result=node(state)
        except Exception:
            emit('failed');raise
        emit('complete');return result
    return wrapped

def build(observe=False):
    graph=StateGraph(MindState)
    for name,node in [('recall',recall),('intent',intent),('search',search),('respond',respond),('save',save)]:
        graph.add_node(name,observe_node(name,node) if observe else node)
    graph.add_edge(START,'recall');graph.add_edge('recall','intent')
    graph.add_conditional_edges('intent',lambda s:'search' if s['intent']=='search' else 'respond',{'search':'search','respond':'respond'})
    graph.add_edge('search','respond');graph.add_edge('respond','save');graph.add_edge('save',END)
    return graph.compile()

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    try:
        args=json.loads(sys.stdin.read(20000))
        memory.validate_session(args['session'])
        result=build(observe=True).invoke(args,{'recursion_limit':10})
        output={'ok':True,'reply':result['reply'],'intent':result['intent'],
                'tools':result.get('agent_tools',[]),'route':result.get('route')}
    except Exception as exc:
        output={'ok':False,'error':str(exc)[:500]}
    print(json.dumps(output,ensure_ascii=False))
    sys.exit(0 if output['ok'] else 1)
