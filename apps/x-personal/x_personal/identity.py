"""Bind an explicitly confirmed Windows account SID to Ibrahim's display name."""
import csv
import hmac
import json
import subprocess
from pathlib import Path
from . import hello

SETTINGS = Path(__file__).resolve().parents[1] / 'settings.json'
POLICY = SETTINGS.with_name('identity-policy.json')


def verification_enabled():
    if not POLICY.exists():
        return True
    return json.loads(POLICY.read_text(encoding='utf-8-sig')).get('verification_required') is not False


def load_settings():
    return json.loads(SETTINGS.read_text(encoding='utf-8-sig'))


def current_account():
    result = subprocess.run(['whoami.exe', '/user', '/fo', 'csv', '/nh'], capture_output=True,
                            text=True, check=True, timeout=10)
    rows = list(csv.reader(result.stdout.strip().splitlines()))
    if len(rows) != 1 or len(rows[0]) != 2 or not rows[0][1].startswith('S-1-'):
        raise RuntimeError('Cannot determine current Windows SID.')
    return {'account': rows[0][0], 'sid': rows[0][1]}


def enroll():
    settings = load_settings()
    if settings.get('expected_windows_sid'):
        raise PermissionError('An account is already enrolled; no automatic overwrite is allowed.')
    account = current_account()
    print('سيتم ربط الاسم إبراهيم بحساب Windows الحالي:', account['account'])
    if input('اكتب إبراهيم لتأكيد الربط: ').strip() != 'إبراهيم':
        raise PermissionError('Enrollment canceled.')
    if hello.verify('X: link this Windows account to Ibrahim.') is not True:
        raise PermissionError('Windows Hello did not confirm enrollment.')
    settings['expected_windows_sid'] = account['sid']
    SETTINGS.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding='utf-8')
    print('تم ربط الحساب بعد تحقق Windows Hello.')


def require_identity():
    if not verification_enabled():
        return
    expected = load_settings().get('expected_windows_sid', '')
    if not expected:
        raise PermissionError('اربط حسابك أولًا باستخدام: X.cmd enroll')
    actual = current_account()['sid']
    if not hmac.compare_digest(expected, actual):
        raise PermissionError('حساب Windows الحالي مختلف عن حساب إبراهيم المسجل.')
    if hello.verify('X: confirm Ibrahim\u2019s Windows account before this interaction.') is not True:
        raise PermissionError('Windows Hello did not confirm the user.')
