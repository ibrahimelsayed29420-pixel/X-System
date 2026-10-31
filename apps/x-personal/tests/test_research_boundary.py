import unittest
from unittest.mock import patch
from x_personal.research import research

class ResearchBoundaryTests(unittest.TestCase):
    def test_unreviewed_channel_never_starts_worker(self):
        with patch('x_personal.research.subprocess.run') as run:
            with self.assertRaises(ValueError):
                research('facebook', 'read', 'https://facebook.com/')
            run.assert_not_called()

    def test_canceled_identity_prevents_research(self):
        from x_personal import __main__ as cli
        with patch('sys.argv', ['X', 'research', '--query', 'Ajman']), \
             patch.object(cli, 'require_identity', side_effect=RuntimeError('canceled')), \
             patch('x_personal.research.research') as fetch:
            with self.assertRaises(RuntimeError):
                cli.main()
            fetch.assert_not_called()

    def test_canceled_identity_prevents_workflow(self):
        from x_personal import __main__ as cli
        with patch('sys.argv', ['X', 'workflow', '--query', 'Ajman']), \
             patch.object(cli, 'require_identity', side_effect=RuntimeError('canceled')), \
             patch('x_personal.workflow.run_workflow') as run:
            with self.assertRaises(RuntimeError):
                cli.main()
            run.assert_not_called()
