import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration,ChatResult
from deepagent_worker import ALLOWED,Boundary,Observer,make_agent

class ScriptedModel(BaseChatModel):
    responses:list
    seen_tools:list=[]
    @property
    def _llm_type(self):return 'test-local'
    def bind_tools(self,tools,**kwargs):
        self.seen_tools=[t.get('name') if isinstance(t,dict) else t.name for t in tools]
        return self
    def _generate(self,messages,stop=None,run_manager=None,**kwargs):
        return ChatResult(generations=[ChatGeneration(message=self.responses.pop(0))])

class DeepAgentTests(unittest.TestCase):
    def test_deepagents_executes_selected_read_tool_and_returns(self):
        observer=Observer(False)
        model=ScriptedModel(responses=[
            AIMessage(content='',tool_calls=[{'name':'search_public_web','args':{'query':'Ajman official real estate'},'id':'call1'}]),
            AIMessage(content='نتيجة البحث')])
        search=Mock(return_value={'ok':True,'items':[{'title':'Official','url':'https://ajmanre.gov.ae','text':'public'}]})
        agent=make_agent(model,observer,search_fn=search)
        result=agent.invoke({'messages':[{'role':'user','content':'ابحث عن عقارات عجمان'}]},{'recursion_limit':8})
        self.assertEqual(result['messages'][-1].content,'نتيجة البحث')
        search.assert_called_once()
        self.assertTrue(set(model.seen_tools)<=ALLOWED)
        self.assertEqual(observer.calls[0]['name'],'search_public_web')

    def test_deepagents_reads_requested_public_page_and_records_source(self):
        with tempfile.TemporaryDirectory() as folder,patch('deepagent_worker.RUNTIME',Path(folder)):
            observer=Observer(True)
            model=ScriptedModel(responses=[
                AIMessage(content='',tool_calls=[{'name':'read_public_page','args':{'url':'https://example.com/'},'id':'page1'}]),
                AIMessage(content='الصفحة تعرض Example Domain')])
            page_read=Mock(return_value={'ok':True,'url':'https://example.com/','title':'Example Domain',
                                         'text':'Example Domain page content','characters':26})
            agent=make_agent(model,observer,page_read_fn=page_read)
            result=agent.invoke({'messages':[{'role':'user','content':'اقرأ https://example.com/'}]},{'recursion_limit':8})
            self.assertEqual(result['messages'][-1].content,'الصفحة تعرض Example Domain')
            page_read.assert_called_once_with('https://example.com/')
            self.assertIn('read_public_page',model.seen_tools)
            self.assertEqual(observer.pages[0]['title'],'Example Domain')
            self.assertEqual(observer.sources,['https://example.com/'])
            self.assertEqual(observer.calls[0]['name'],'read_public_page')
            trace=json.loads((Path(folder)/'agent-trace.json').read_text(encoding='utf-8'))
            self.assertEqual(trace['pages'][0]['url'],'https://example.com/')

    def test_boundary_rejects_shell_without_dispatch(self):
        middleware=Boundary(Observer(False));handler=Mock()
        result=middleware.wrap_tool_call(SimpleNamespace(tool_call={'name':'execute','id':'nope'}),handler)
        self.assertEqual(result.status,'error');handler.assert_not_called()

    def test_private_query_never_reaches_search_provider(self):
        observer=Observer(False)
        model=ScriptedModel(responses=[
            AIMessage(content='',tool_calls=[{'name':'search_public_web','args':{'query':'ibrahim@example.com'},'id':'call1'}]),
            AIMessage(content='الطلب مرفوض')])
        search=Mock()
        agent=make_agent(model,observer,search_fn=search)
        with self.assertRaises(ValueError):
            agent.invoke({'messages':[{'role':'user','content':'اختبار حد الخصوصية'}]},{'recursion_limit':8})
        search.assert_not_called()

if __name__=='__main__':unittest.main()
