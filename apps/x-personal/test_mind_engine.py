import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import mind_worker as mind
from x_personal import memory

class MindTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        p=patch.object(memory,'DATABASE',Path(folder.name)/'memory.sqlite')
        p.start();self.addCleanup(p.stop)
        skills=patch.object(mind.skill_graph,'DATABASE',Path(folder.name)/'skills.sqlite')
        skills.start();self.addCleanup(skills.stop)
        semantic=patch.object(mind.semantic_memory,'retrieve',return_value={'ok':False,'items':[]})
        semantic.start();self.addCleanup(semantic.stop)
        deep=patch.object(mind.deep_reasoning,'enabled',return_value=False)
        deep.start();self.addCleanup(deep.stop)

    def run_turn(self,text,session='test'):
        return mind.build().invoke({'text':text,'model':'test-model','session':session})

    def test_explicit_memory_persists_and_can_be_forgotten(self):
        with patch.object(mind.brain,'generate') as generate,patch.object(mind,'research') as search:
            self.run_turn('احفظ أفضل الردود القصيرة')
            self.assertEqual(memory.facts()[0]['content'],'أفضل الردود القصيرة')
            self.assertIn('أفضل الردود القصيرة',self.run_turn('ذاكرتك')['reply'])
            self.run_turn('انس '+str(memory.facts()[0]['id']))
            self.assertEqual(memory.facts(),[])
            generate.assert_not_called();search.assert_not_called()

    def test_history_is_local_and_session_scoped(self):
        with patch.object(mind.brain,'generate',return_value='رد محلي') as generate,patch.object(mind,'research') as search:
            self.run_turn('طلب أول')
            self.run_turn('نكمل كلامنا')
            self.assertEqual(len(generate.call_args.args[2]),2)
            self.assertEqual(memory.history('other'),[])
            self.assertEqual(memory.facts(),[])
            search.assert_not_called()

    def test_explicit_search_supplies_evidence_and_source_links(self):
        with patch.object(mind,'research',return_value={'ok':True,'items':[{'title':'Source','url':'https://example.com','text':'sample'}]}) as search, \
             patch.object(mind.brain,'generate',return_value='ملخص') as generate:
            result=self.run_turn('ابحث عن سوق عجمان')
            search.assert_called_once_with('web','search','سوق عجمان',3)
            self.assertIn('https://example.com',result['reply'])
            self.assertTrue(generate.call_args.args[4]['ok'])

    def test_failed_search_is_not_a_fabricated_answer(self):
        with patch.object(mind,'research',return_value={'ok':False,'error':{'code':'RATE_LIMITED'}}), \
             patch.object(mind.brain,'generate') as generate:
            result=self.run_turn('ابحث عن سوق عجمان')
            self.assertIn('ما نجحتش',result['reply']);generate.assert_not_called()

    def test_no_shell_or_account_action_route(self):
        with patch.object(mind.brain,'generate',return_value='أقدر أجهز المسودة بس') as generate, \
             patch.object(mind,'research') as search:
            result=self.run_turn('ابعت الإعلان على واتساب')
            self.assertEqual(result['intent'],'chat');search.assert_not_called()

    def test_identity_does_not_depend_on_model_guess(self):
        with patch.object(mind.brain,'generate') as generate:
            reply=self.run_turn('إنت اسمك إيه؟')['reply']
            self.assertIn('أنا إكس',reply)
            generate.assert_not_called()

    def test_english_memory_and_identity_commands(self):
        with patch.object(mind.brain,'generate') as generate:
            self.assertIn("I'm X",self.run_turn('Who are you?')['reply'])
            self.run_turn('Remember I work in Arabic and English')
            self.assertIn('Arabic and English',self.run_turn('show memory')['reply'])
            number=memory.facts()[0]['id']
            self.run_turn('forget '+str(number))
            self.assertEqual(memory.facts(),[])
            generate.assert_not_called()

    def test_enabled_deep_agent_is_used_from_conversation(self):
        with patch.object(mind.deep_reasoning,'enabled',return_value=True), \
             patch.object(mind.deep_reasoning,'respond',return_value={'reply':'Tool-backed answer','tools':[{'name':'search_public_web','state':'complete'}]}) as deep, \
             patch.object(mind,'research') as old_search:
            result=self.run_turn('Search for Ajman official market sources')
            self.assertEqual(result['reply'],'Tool-backed answer')
            self.assertEqual(result['agent_tools'][0]['name'],'search_public_web')
            deep.assert_called_once();old_search.assert_not_called()

if __name__=='__main__':unittest.main()
