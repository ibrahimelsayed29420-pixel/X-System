import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock,patch
from x_personal import identity
from x_personal.__main__ import main
from setup_speech_model import safe_member


class IdentityBoundaryTests(unittest.TestCase):
    def setUp(self):
        policy=patch.object(identity,'verification_enabled',return_value=True)
        policy.start()
        self.addCleanup(policy.stop)

    def test_no_enrollment_never_prompts_or_authorizes(self):
        with patch.object(identity, 'load_settings', return_value={}), patch.object(identity.hello, 'verify') as verify:
            with self.assertRaises(PermissionError):
                identity.require_identity()
            verify.assert_not_called()

    def test_different_account_is_denied_before_hello(self):
        with patch.object(identity, 'load_settings', return_value={'expected_windows_sid': 'S-1-5-21-a'}), \
             patch.object(identity, 'current_account', return_value={'sid': 'S-1-5-21-b'}), \
             patch.object(identity.hello, 'verify') as verify:
            with self.assertRaises(PermissionError):
                identity.require_identity()
            verify.assert_not_called()

    def test_canceled_hello_does_not_record_or_call_model(self):
        with patch('sys.argv', ['x', 'chat']), patch('builtins.input', return_value=''), \
             patch('x_personal.__main__.require_identity', side_effect=PermissionError('Canceled')), \
             patch('x_personal.__main__.ArabicListener') as listener, \
             patch('x_personal.__main__.brain.answer') as answer:
            with self.assertRaises(PermissionError):
                main()
            listener.assert_not_called()
            answer.assert_not_called()

    def test_mind_open_launches_the_local_chat_page(self):
        response=MagicMock()
        response.__enter__.return_value.read.return_value=json.dumps({'chat_available':True}).encode()
        with patch('sys.argv',['x','mind-open']), \
             patch('x_personal.__main__.require_identity'), \
             patch('x_personal.mind_runtime.ensure_started') as ensure_started, \
             patch('urllib.request.urlopen',return_value=response) as urlopen, \
             patch('webbrowser.open_new_tab',return_value=True) as open_tab:
            main()
        ensure_started.assert_called_once()
        urlopen.assert_called_once_with('http://127.0.0.1:18764/api/state',timeout=1)
        open_tab.assert_called_once_with('http://127.0.0.1:18764/')

    def test_mind_open_gracefully_restarts_idle_outdated_service(self):
        old_response=MagicMock()
        old_response.__enter__.return_value.read.return_value=json.dumps({'chat_available':False}).encode()
        new_response=MagicMock()
        new_response.__enter__.return_value.read.return_value=json.dumps({'chat_available':True}).encode()
        with tempfile.TemporaryDirectory() as folder:
            data=Path(folder)
            (data/'inbox').mkdir()
            with patch('sys.argv',['x','mind-open']), \
                 patch('x_personal.__main__.require_identity'), \
                 patch('x_personal.mind_runtime.DATA',data), \
                 patch('x_personal.mind_runtime.ensure_started') as ensure_started, \
                 patch('x_personal.mind_runtime.status',side_effect=[
                     {'state':'ready','process_alive':True},
                     {'state':'stopped','process_alive':False},
                     {'state':'ready','process_alive':True},
                 ]), \
                 patch('urllib.request.urlopen',side_effect=[old_response,new_response]), \
                 patch('webbrowser.open_new_tab',return_value=True), \
                 patch('time.sleep'):
                main()
            self.assertEqual(ensure_started.call_count,2)
            self.assertTrue((data/'stop.request').is_file())

    def test_mind_open_does_not_restart_service_while_busy(self):
        response=MagicMock()
        response.__enter__.return_value.read.return_value=json.dumps({'chat_available':False}).encode()
        with patch('sys.argv',['x','mind-open']), \
             patch('x_personal.__main__.require_identity'), \
             patch('x_personal.mind_runtime.ensure_started') as ensure_started, \
             patch('x_personal.mind_runtime.status',return_value={'state':'processing','process_alive':True}), \
             patch('urllib.request.urlopen',return_value=response), \
             patch('webbrowser.open_new_tab') as open_tab:
            with self.assertRaisesRegex(RuntimeError,'يعالج طلبًا'):
                main()
        ensure_started.assert_called_once()
        open_tab.assert_not_called()

    def test_failed_enrollment_leaves_settings_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.json'
            original = '{"display_name":"Ibrahim","expected_windows_sid":""}'
            path.write_text(original, encoding='utf-8')
            with patch.object(identity, 'SETTINGS', path), \
                 patch.object(identity, 'current_account', return_value={'account':'test', 'sid':'S-1-5-test'}), \
                 patch('builtins.input', return_value='إبراهيم'), \
                 patch.object(identity.hello, 'verify', side_effect=PermissionError('Canceled')):
                with self.assertRaises(PermissionError):
                    identity.enroll()
            self.assertEqual(path.read_text(encoding='utf-8'), original)

    def test_nonaffirmative_hello_result_is_denied(self):
        with patch.object(identity, 'load_settings', return_value={'expected_windows_sid':'S-1-5-21-a'}), \
             patch.object(identity, 'current_account', return_value={'sid':'S-1-5-21-a'}), \
             patch.object(identity.hello, 'verify', return_value=False):
            with self.assertRaises(PermissionError):
                identity.require_identity()


class DownloadBoundaryTests(unittest.TestCase):
    def test_path_escape_is_rejected(self):
        for name in ['../bad', '/bad', 'C:/bad', 'vosk-model-ar-mgb2-0.4/../../bad', 'other/model']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                safe_member(name)

    def test_expected_model_path_is_accepted(self):
        self.assertEqual(str(safe_member('vosk-model-ar-mgb2-0.4/am/final.mdl')),
                         'vosk-model-ar-mgb2-0.4/am/final.mdl')


if __name__ == '__main__':
    unittest.main()
