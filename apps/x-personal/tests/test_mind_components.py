import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
from x_personal import brain,identity,skill_graph

class MindComponentsTests(unittest.TestCase):
    def test_chat_uses_a_smaller_context_and_concise_default_reply(self):
        with patch.object(brain,'gemini_api_key',return_value=None), \
             patch.object(brain,'models',return_value=['local-model']), \
             patch.object(brain,'system_prompt',return_value='X persona'), \
             patch.object(brain,'local_request',return_value={'message':{'content':'أهلًا'}}) as request:
            self.assertEqual(brain.generate('مرحبًا','local-model'),'أهلًا')

        payload=request.call_args.args[1]
        self.assertEqual(payload['options']['num_ctx'],4096)
        self.assertEqual(payload['options']['num_predict'],128)
        self.assertEqual(payload['keep_alive'],'10m')
        self.assertEqual(request.call_args.kwargs['timeout'],240)
        self.assertIn('اختصرها في جملة أو جملتين',payload['messages'][0]['content'])

    def test_chat_uses_gemini_when_a_key_is_configured(self):
        route={}
        with patch.object(brain,'gemini_api_key',return_value='test-key'), \
             patch.object(brain,'system_prompt',return_value='X persona'), \
             patch.object(brain,'gemini_request',return_value='Gemini answer') as request, \
             patch.object(brain,'local_request') as local:
            self.assertEqual(
                brain.generate('مرحبًا','local-model',route=route),
                'Gemini answer',
            )
        self.assertEqual(route['provider'],'gemini')
        self.assertEqual(request.call_args.args[0],'test-key')
        self.assertNotIn('test-key',str(route))
        local.assert_not_called()

    def test_gemini_failure_falls_back_to_ollama_and_records_the_reason(self):
        route={}
        with patch.object(brain,'gemini_api_key',return_value='test-key'), \
             patch.object(brain,'system_prompt',return_value='X persona'), \
             patch.object(brain,'gemini_request',
                          side_effect=brain.GeminiUnavailable('Gemini request failed')), \
             patch.object(brain,'models',return_value=['local-model']), \
             patch.object(brain,'local_request',
                          return_value={'message':{'content':'Local answer'}}):
            self.assertEqual(
                brain.generate('مرحبًا','local-model',route=route),
                'Local answer',
            )
        self.assertEqual(route['provider'],'ollama')
        self.assertEqual(route['fallback_reason'],'Gemini request failed')

    def test_gemini_rest_request_keeps_key_out_of_url_and_parses_reply(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self,*args):
                return False

            def read(self,limit):
                return b'{"candidates":[{"content":{"parts":[{"text":"Hello"}]}}]}'

        with patch.object(brain.urllib.request,'urlopen',return_value=Response()) as open_request:
            self.assertEqual(
                brain.gemini_request(
                    'test-key',
                    [
                        {'role':'system','content':'System rules'},
                        {'role':'user','content':'Hi'},
                    ],
                ),
                'Hello',
            )
        request=open_request.call_args.args[0]
        self.assertEqual(request.full_url,
                         'https://generativelanguage.googleapis.com/v1beta/models/'
                         'gemini-flash-latest:generateContent')
        self.assertEqual(request.get_header('X-goog-api-key'),'test-key')
        self.assertNotIn('test-key',request.full_url)
        self.assertEqual(open_request.call_args.kwargs['timeout'],45)

    def test_gemini_retries_a_transient_service_error(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self,*args):
                return False

            def read(self,limit):
                return b'{"candidates":[{"content":{"parts":[{"text":"Hello"}]}}]}'

        failure=urllib.error.HTTPError(
            'https://generativelanguage.googleapis.com/',503,'Unavailable',{},None
        )
        with patch.object(brain.urllib.request,'urlopen',
                          side_effect=[failure,failure,Response()]) as open_request, \
             patch.object(brain.time,'sleep') as sleep, \
             patch.object(brain.random,'random',return_value=0.1):
            self.assertEqual(
                brain.gemini_request(
                    'test-key',
                    [
                        {'role':'system','content':'System rules'},
                        {'role':'user','content':'Hi'},
                    ],
                ),
                'Hello',
            )
        self.assertEqual(open_request.call_count,3)
        self.assertEqual(sleep.call_count,2)

    def test_gemini_rate_limit_retries_then_uses_local_fallback(self):
        route={}
        failure=urllib.error.HTTPError(
            'https://generativelanguage.googleapis.com/',429,'Rate limited',{},None
        )
        with patch.object(brain,'gemini_api_key',return_value='test-key'), \
             patch.object(brain,'system_prompt',return_value='X persona'), \
             patch.object(brain.urllib.request,'urlopen',side_effect=failure), \
             patch.object(brain.time,'sleep'), \
             patch.object(brain.random,'random',return_value=0.1), \
             patch.object(brain,'models',return_value=['local-model']), \
             patch.object(brain,'local_request',
                          return_value={'message':{'content':'Local answer'}}):
            self.assertEqual(
                brain.generate('مرحبًا','local-model',route=route),
                'Local answer',
            )
        self.assertEqual(
            route['fallback_reason'],
            'Gemini request failed (HTTP 429 after 3 attempts)',
        )

    def test_denied_credential_store_access_falls_back_to_ollama(self):
        route={}
        with patch.object(brain,'gemini_api_key',side_effect=PermissionError), \
             patch.object(brain,'system_prompt',return_value='X persona'), \
             patch.object(brain,'models',return_value=['local-model']), \
             patch.object(brain,'local_request',
                          return_value={'message':{'content':'Local answer'}}):
            self.assertEqual(
                brain.generate('مرحبًا','local-model',route=route),
                'Local answer',
            )
        self.assertEqual(route['provider'],'ollama')
        self.assertEqual(
            route['fallback_reason'],
            'Windows Credential Manager access was denied',
        )

    def test_development_policy_skips_windows_verification(self):
        with patch.object(identity,'verification_enabled',return_value=False), \
             patch.object(identity,'current_account') as account,patch.object(identity.hello,'verify') as hello:
            identity.require_identity()
            account.assert_not_called();hello.assert_not_called()

    def test_lessons_link_related_skills_and_forget_removes_edges(self):
        with tempfile.TemporaryDirectory() as folder:
            db=Path(folder)/'skills.sqlite'
            key=skill_graph.learn('كل مهارة بحث تعتمد على مصادر موثقة',db)
            graph=skill_graph.snapshot(db)
            links=[e for e in graph['relations'] if e['source']==key]
            self.assertTrue(any(e['target']=='research' for e in links))
            self.assertTrue(any(e['target']=='workflow' for e in links))
            skill_graph.forget_lesson('كل مهارة بحث تعتمد على مصادر موثقة',db)
            self.assertFalse(any(e['source']==key for e in skill_graph.snapshot(db)['relations']))

    def test_observed_success_is_idempotent_and_failure_is_kept(self):
        with tempfile.TemporaryDirectory() as folder:
            db=Path(folder)/'skills.sqlite'
            skill_graph.record('one','search',True,path=db)
            skill_graph.record('one','search',True,path=db)
            skill_graph.record('two','search',False,'test failure',path=db)
            graph=skill_graph.snapshot(db)
            outcome=next(row for row in graph['outcomes'] if row['skill']=='research')
            self.assertEqual(outcome['attempts'],2);self.assertEqual(outcome['successful'],1)

    def test_selected_route_is_recorded_under_its_skill(self):
        with tempfile.TemporaryDirectory() as folder:
            db=Path(folder)/'skills.sqlite'
            skill_graph.record('planner-run','planning',True,path=db)
            skill_graph.record('property-run','real_estate',True,path=db)
            graph=skill_graph.snapshot(db)
            outcome=next(row for row in graph['outcomes'] if row['skill']=='planning')
            self.assertEqual(outcome['attempts'],1)
            property_outcome=next(row for row in graph['outcomes'] if row['skill']=='real_estate')
            self.assertEqual(property_outcome['attempts'],1)
