import json
import io
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import mind_dashboard
from x_personal import learning, skill_graph


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.database = self.root / 'learning.sqlite'
        self.graph = self.root / 'skills.sqlite'
        self.skills = self.root / 'approved'

    def add_source(self, content='خطوات البحث عن مصادر موثوقة'):
        folder = self.root / 'materials'
        folder.mkdir(exist_ok=True)
        (folder / 'workflow.md').write_text(content, encoding='utf-8')
        source_id = learning.add_folder_source(
            str(folder), own_materials=True, path=self.database
        )
        return folder, source_id

    def make_proposal(self, source_id):
        result = learning.scan_source(
            source_id,
            path=self.database,
            summarize_fn=lambda documents: {
                'is_skill': True,
                'title': 'بحث موثوق',
                'description': 'خطوات قابلة لإعادة الاستخدام للبحث.',
                'steps': ['حدد السؤال بوضوح.', 'تحقق من المصادر المستقلة.'],
                'tags': ['search', 'research'],
            },
        )
        return result['proposal_id']

    def test_activity_learning_is_bounded_and_can_be_erased(self):
        tools = [
            {'name': 'search_public_web', 'state': 'complete'},
            {'name': 'execute', 'state': 'complete'},
        ]
        for request_id in ('one', 'two', 'three'):
            learning.record_x_activity(request_id, 'search', tools, True, self.database)

        with learning.connect(self.database) as db:
            columns = {row['name'] for row in db.execute('PRAGMA table_info(activity)')}
        self.assertEqual(columns, {'id', 'signature', 'intent', 'tools', 'ok', 'at'})
        state = learning.snapshot(self.database)
        self.assertEqual(state['activity_count'], 3)
        self.assertEqual(len([p for p in state['proposals'] if p['status'] == 'pending']), 1)
        self.assertNotIn('execute', json.dumps(state, ensure_ascii=False))

        self.assertFalse(learning.set_activity_capture(False, self.database))
        state = learning.snapshot(self.database)
        self.assertEqual(state['activity_count'], 0)
        self.assertFalse(any(p['source_id'] == 'x_activity' for p in state['proposals']))

        self.assertIsNone(
            learning.record_x_activity('four', 'search', tools, True, self.database)
        )

    def test_folder_source_requires_permission_and_redacts_sensitive_content(self):
        folder = self.root / 'materials'
        folder.mkdir()
        (folder / 'workflow.md').write_text(
            'Password=supersecret\\nContact private@example.com +1 555 123 4567',
            encoding='utf-8',
        )
        (folder / '.env').write_text('TOKEN=hidden', encoding='utf-8')
        (folder / 'secret-notes.txt').write_text('hidden notes', encoding='utf-8')

        with self.assertRaises(ValueError):
            learning.add_folder_source(str(folder), path=self.database)
        with self.assertRaises(ValueError):
            learning.add_folder_source(
                str(Path(folder.anchor)), own_materials=True, path=self.database
            )

        source_id = learning.add_folder_source(
            str(folder), own_materials=True, path=self.database
        )
        captured = []

        def summarize(documents):
            captured.extend(documents)
            return {
                'is_skill': True,
                'title': 'بحث موثوق',
                'description': 'خطوات قابلة لإعادة الاستخدام للبحث.',
                'steps': ['حدد السؤال بوضوح.', 'تحقق من المصادر المستقلة.'],
                'tags': ['search'],
            }

        result = learning.scan_source(
            source_id, path=self.database, summarize_fn=summarize
        )
        self.assertEqual(result['files_read'], 1)
        self.assertEqual(len(captured), 1)
        self.assertNotIn('supersecret', captured[0]['content'])
        self.assertNotIn('private@example.com', captured[0]['content'])
        self.assertNotIn('555 123 4567', captured[0]['content'])
        self.assertIn('[REDACTED]', captured[0]['content'])
        self.assertIn('[REDACTED EMAIL]', captured[0]['content'])
        self.assertIn('[REDACTED PHONE]', captured[0]['content'])
        self.assertEqual(captured[0]['path'], 'workflow.md')

    def test_approval_exposes_only_approved_skill_files_and_removal_cleans_graph(self):
        _, source_id = self.add_source()
        proposal_id = self.make_proposal(source_id)
        approved = learning.approve_proposal(
            proposal_id,
            path=self.database,
            skills_dir=self.skills,
            graph_path=self.graph,
        )
        skill_file = Path(approved['path'])
        self.assertTrue(skill_file.is_file())
        self.assertIn('## الخطوات', skill_file.read_text(encoding='utf-8'))
        self.assertTrue(
            any(skill['id'] == approved['skill_id']
                for skill in skill_graph.snapshot(self.graph)['skills'])
        )

        utils = types.ModuleType('deepagents.backends.utils')
        utils.create_file_data = lambda content: {'content': content}
        backends = types.ModuleType('deepagents.backends')
        deepagents = types.ModuleType('deepagents')
        with patch.dict('sys.modules', {
            'deepagents': deepagents,
            'deepagents.backends': backends,
            'deepagents.backends.utils': utils,
        }):
            payload = learning.skill_file_payload(self.skills)
        virtual_path = f"/skills/project/{skill_file.parent.name}/SKILL.md"
        self.assertIn(virtual_path, payload)
        self.assertIn('بحث موثوق', payload[virtual_path]['content'])

        learning.remove_approved_skill(
            approved['skill_id'],
            path=self.database,
            skills_dir=self.skills,
            graph_path=self.graph,
        )
        self.assertFalse(skill_file.exists())
        self.assertFalse(
            any(skill['id'] == approved['skill_id']
                for skill in skill_graph.snapshot(self.graph)['skills'])
        )

    def test_revoking_source_removes_its_approved_skill(self):
        _, source_id = self.add_source()
        proposal_id = self.make_proposal(source_id)
        approved = learning.approve_proposal(
            proposal_id,
            path=self.database,
            skills_dir=self.skills,
            graph_path=self.graph,
        )

        learning.revoke_source(
            source_id,
            path=self.database,
            skills_dir=self.skills,
            graph_path=self.graph,
        )

        self.assertFalse(Path(approved['path']).exists())
        state = learning.snapshot(self.database)
        self.assertEqual(state['sources'][0]['locator'], '')
        self.assertFalse(state['proposals'])
        self.assertFalse(
            any(skill['id'] == approved['skill_id']
                for skill in skill_graph.snapshot(self.graph)['skills'])
        )

    def test_rejecting_proposal_does_not_create_a_skill(self):
        _, source_id = self.add_source()
        proposal_id = self.make_proposal(source_id)

        learning.reject_proposal(proposal_id, path=self.database)

        self.assertFalse(learning.snapshot(self.database)['proposals'])
        self.assertFalse(self.skills.exists())

    def test_dashboard_learning_post_requires_local_origin(self):
        port = 18764
        origin = f'http://127.0.0.1:{port}'
        body = json.dumps({'action': 'set_capture', 'enabled': False}).encode()

        with patch.object(
            mind_dashboard.learning, 'set_activity_capture', return_value=False
        ) as set_capture:
            request = _FakePostRequest(
                port, body, {'Host': f'127.0.0.1:{port}',
                             'Origin': origin, 'Content-Type': 'application/json',
                             'Content-Length': str(len(body))}
            )
            mind_dashboard.Handler.do_POST(request)
            self.assertEqual(request.response[1], 200)
            self.assertTrue(request.response[0]['ok'])
            set_capture.assert_called_once_with(False)

            request = _FakePostRequest(
                port, body, {'Host': f'127.0.0.1:{port}',
                             'Origin': 'http://attacker.example',
                             'Content-Type': 'application/json',
                             'Content-Length': str(len(body))}
            )
            mind_dashboard.Handler.do_POST(request)
            self.assertEqual(request.error_code, 403)
            set_capture.assert_called_once()


class _FakePostRequest:
    def __init__(self, port, body, headers):
        self.server = SimpleNamespace(server_port=port)
        self.headers = headers
        self.path = '/api/learning'
        self.rfile = io.BytesIO(body)
        self.response = None
        self.error_code = None

    def _allowed_request(self, require_origin=False):
        return mind_dashboard.Handler._allowed_request(self, require_origin)

    def _learning_action(self, action, data):
        return mind_dashboard.Handler._learning_action(self, action, data)

    def _json(self, value, status_code=200):
        self.response = (value, status_code)

    def send_error(self, code, message=None):
        self.error_code = code


if __name__ == '__main__':
    unittest.main()
