import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import mind_service
from x_personal import learning, mind_runtime

class RuntimeFileTests(unittest.TestCase):
    def test_windows_transient_reader_does_not_abort_atomic_write(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'status.json'
            original=Path.replace
            attempts=[]
            def locked_then_released(source,destination):
                attempts.append(1)
                if len(attempts)<3:raise PermissionError('transient Windows reader')
                return original(source,destination)
            with patch.object(Path,'replace',locked_then_released):
                mind_service.atomic(target,{'state':'ready'})
            self.assertIn('ready',target.read_text())

    def test_status_write_permission_error_is_explicit(self):
        with patch.object(mind_service,'atomic',side_effect=PermissionError('locked')):
            with self.assertRaisesRegex(PermissionError,'locked'):
                mind_service.state('ready')

    def test_runtime_state_uses_per_user_local_app_data(self):
        self.assertEqual(
            mind_runtime.DATA,
            mind_runtime.LOCAL_APP_DATA/'X-System'/'mind'/'runtime',
        )
        self.assertEqual(
            learning.DATABASE,
            mind_runtime.LOCAL_APP_DATA/'X-System'/'mind'/'learning.sqlite',
        )

    def test_legacy_runtime_migration_is_safe_and_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            legacy=root/'legacy'
            target=root/'local'
            legacy_runtime=legacy/'runtime'
            (legacy_runtime/'inbox').mkdir(parents=True)
            (legacy_runtime/'results').mkdir()
            request_id='a'*32
            queued=legacy_runtime/'inbox'/(request_id+'.json')
            queued.write_text('{"payload":{"text":"preserve"}}',encoding='utf-8')
            (legacy_runtime/'inbox'/(('b'*32)+'.working')).write_text(
                '{"payload":{"text":"recover"}}',encoding='utf-8'
            )
            result_id='01234567-89ab-cdef-0123-456789abcdef'
            result=legacy_runtime/'results'/(result_id+'.json')
            result.write_text('{"ok":true}',encoding='utf-8')
            (legacy_runtime/'events.jsonl').write_text('{"stage":"agent"}\n',encoding='utf-8')
            (legacy_runtime/'status.json').write_text('{"pid":1}',encoding='utf-8')
            (legacy_runtime/'stop.request').write_text('stop',encoding='utf-8')
            with learning.connect(legacy_runtime/'learning.sqlite') as db:
                db.execute(
                    "INSERT INTO settings(key,value) VALUES ('capture_x_activity','false')"
                )
            old_skill=legacy/'skills'/'approved'/f'learned-{"c"*12}'
            old_skill.mkdir(parents=True)
            (old_skill/'SKILL.md').write_text('# Approved',encoding='utf-8')

            paths=mind_runtime.migrate_legacy_data(target,legacy)
            new_runtime=Path(paths['runtime'])
            self.assertEqual(
                (new_runtime/'recovered'/'inbox'/(request_id+'.json.paused')).read_text(encoding='utf-8'),
                queued.read_text(encoding='utf-8'),
            )
            self.assertTrue((new_runtime/'recovered'/'inbox'/(('b'*32)+'.working.paused')).exists())
            self.assertFalse(list((new_runtime/'inbox').glob('*.json')))
            self.assertEqual(
                (new_runtime/'results'/(result_id+'.json')).read_text(encoding='utf-8'),
                result.read_text(encoding='utf-8'),
            )
            self.assertTrue((new_runtime/'events.jsonl').is_file())
            self.assertFalse((new_runtime/'status.json').exists())
            self.assertFalse((new_runtime/'stop.request').exists())
            self.assertTrue((Path(paths['approved_skills'])/f'learned-{"c"*12}'/'SKILL.md').is_file())
            with learning.connect(target/'learning.sqlite') as db:
                setting=db.execute(
                    "SELECT value FROM settings WHERE key='capture_x_activity'"
                ).fetchone()
            self.assertEqual(setting['value'],'false')
            self.assertTrue(queued.exists())

            migrated_event=new_runtime/'events.jsonl'
            migrated_event.write_text('keep destination',encoding='utf-8')
            mind_runtime.migrate_legacy_data(target,legacy)
            self.assertEqual(migrated_event.read_text(encoding='utf-8'),'keep destination')
