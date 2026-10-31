import tempfile
import unittest
from pathlib import Path
from workflow_worker import execute

def success(state):
    return {'research_result': {'ok':True,'items':[
        {'title':'Official source','url':'https://example.com','text':'External source text'},
        {'title':'Duplicate','url':'https://example.com','text':'duplicate'},
        {'title':'Invalid','url':'file:///private','text':'bad'}]}}

class WorkflowTests(unittest.TestCase):
    def test_success_deduplicates_and_persists(self):
        with tempfile.TemporaryDirectory() as folder:
            result = execute('test',data_dir=folder,collector=success)
            self.assertEqual(result['status'],'complete')
            self.assertEqual(len(result['sources']),1)
            self.assertTrue(Path(result['report_path']).is_file())
            again = execute(resume=result['run_id'],data_dir=folder,
                            collector=lambda _:self.fail('Completed task repeated external action'))
            self.assertTrue(again['resumed'])

    def test_failure_never_becomes_success_report(self):
        with tempfile.TemporaryDirectory() as folder:
            result = execute('test',data_dir=folder,collector=lambda _: {
                'research_result':{'ok':False},'status':'failed','error':{'code':'RATE_LIMITED'}})
            self.assertEqual(result['status'],'failed')
            self.assertNotIn('report_path',result)

    def test_interrupted_node_resumes_without_repeating_plan(self):
        with tempfile.TemporaryDirectory() as folder:
            events=[]
            def interrupted(state):
                raise RuntimeError('simulated interruption')
            with self.assertRaises(RuntimeError):
                execute('test',data_dir=folder,collector=interrupted,
                        on_event=lambda run,event:events.append((run,event)))
            run_id = events[0][0]
            resumed=[]
            result = execute(resume=run_id,data_dir=folder,collector=success,
                             on_event=lambda run,event:resumed.extend(event))
            self.assertEqual(result['status'],'complete')
            self.assertNotIn('plan',resumed)

if __name__ == '__main__':
    unittest.main()
