import unittest
from unittest.mock import patch

import mind_worker
from x_personal import deep_reasoning


class MindWorkerRoutingTests(unittest.TestCase):
    def test_explicit_research_always_uses_search_node(self):
        with patch.object(deep_reasoning,'enabled',return_value=True):
            result = mind_worker.intent({'text':'ابحث عن أسعار الإيجارات في عجمان'})
        self.assertEqual(result['intent'],'search')
        self.assertEqual(result['query'],'أسعار الإيجارات في عجمان')

    def test_short_conversation_uses_dialogue_model(self):
        state = {'text':'صباح الخير','model':'x-ibrahim:latest','history':[],'facts':[]}
        with patch.object(deep_reasoning,'enabled',return_value=True), \
             patch.object(deep_reasoning,'model',return_value='x-qwen-agent:latest'), \
             patch.object(deep_reasoning,'respond') as agent, \
             patch.object(mind_worker.brain,'models',return_value=['x-ibrahim:latest']), \
             patch.object(mind_worker.brain,'generate',return_value='أهلًا') as generate:
            result = mind_worker.respond(state)
        agent.assert_not_called()
        self.assertEqual(generate.call_args.args[1],'x-ibrahim:latest')
        self.assertEqual(result['route']['agent'],'dialogue')

    def test_research_uses_local_agent_model_and_cited_evidence(self):
        state = {
            'text':'ابحث عن أسعار الإيجارات في عجمان',
            'model':'x-ibrahim:latest',
            'history':[],
            'facts':[],
            'evidence':{'ok':True,'items':[{'url':'https://example.com','title':'Example','text':'public evidence'}]},
        }
        with patch.object(deep_reasoning,'enabled',return_value=True), \
             patch.object(deep_reasoning,'model',return_value='x-qwen-agent:latest'), \
             patch.object(mind_worker.brain,'models',return_value=['x-qwen-agent:latest']), \
             patch.object(mind_worker.brain,'generate',return_value='نتيجة موثقة') as generate:
            result = mind_worker.respond(state)
        self.assertEqual(generate.call_args.args[1],'x-qwen-agent:latest')
        self.assertEqual(result['route']['agent'],'research-specialist')
        self.assertIn('https://example.com',result['reply'])

    def test_listing_request_uses_fact_preserving_template(self):
        state = {'text':'صغ إعلانًا لهذه الشقة للإيجار','model':'x-ibrahim:latest','history':[],'facts':[]}
        with patch.object(deep_reasoning,'enabled',return_value=True), \
             patch.object(deep_reasoning,'model',return_value='x-qwen-agent:latest'), \
             patch.object(mind_worker.brain,'generate') as generate:
            result = mind_worker.respond(state)
        generate.assert_not_called()
        self.assertEqual(result['route']['model'],'local-template')
        self.assertEqual(result['route']['skill'],'real_estate')
        self.assertIn('مسودة إعلان',result['reply'])

    def test_non_listing_real_estate_request_uses_domain_prompt(self):
        state = {'text':'راجع هذه الشقة للإيجار وحدد البيانات الناقصة','model':'x-ibrahim:latest','history':[],'facts':[]}
        with patch.object(deep_reasoning,'enabled',return_value=True), \
             patch.object(deep_reasoning,'model',return_value='x-qwen-agent:latest'), \
             patch.object(mind_worker.brain,'models',return_value=['x-qwen-agent:latest']), \
             patch.object(mind_worker.brain,'generate',return_value='مراجعة') as generate:
            result = mind_worker.respond(state)
        self.assertEqual(generate.call_args.kwargs['specialty'],'real_estate')
        self.assertEqual(result['route']['skill'],'real_estate')
        self.assertEqual(result['reply'],'مراجعة')

    def test_analytical_request_uses_deep_agents(self):
        state = {'text':'حلل الخيارات المتاحة','model':'x-ibrahim:latest','history':[],'facts':[]}
        with patch.object(deep_reasoning,'enabled',return_value=True), \
             patch.object(deep_reasoning,'model',return_value='x-qwen-agent:latest'), \
             patch.object(deep_reasoning,'respond',return_value={'reply':'تحليل','tools':[]}) as agent:
            result = mind_worker.respond(state)
        self.assertEqual(agent.call_args.args[1]['agent'],'workflow-orchestrator')
        self.assertEqual(result['reply'],'تحليل')


if __name__ == '__main__':
    unittest.main()
