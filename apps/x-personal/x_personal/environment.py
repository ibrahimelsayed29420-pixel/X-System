"""Minimal local inventory, without browser profiles, credentials or file contents."""
import os
import platform
import shutil
import sysconfig
from pathlib import Path
from .identity import current_account


def native_windows_architecture():
    import ctypes as c
    from ctypes import wintypes as w
    kernel = c.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = w.HANDLE
    kernel.IsWow64Process2.argtypes = [w.HANDLE, c.POINTER(w.USHORT), c.POINTER(w.USHORT)]
    kernel.IsWow64Process2.restype = w.BOOL
    process, native = w.USHORT(), w.USHORT()
    if not kernel.IsWow64Process2(kernel.GetCurrentProcess(), c.byref(process), c.byref(native)):
        raise c.WinError(c.get_last_error())
    return {0xAA64: 'ARM64', 0x8664: 'AMD64', 0x014c: 'x86'}.get(native.value, f'unknown-0x{native.value:04x}')


def inspect_environment():
    reference = Path('D:/الهوية - جهاز جديد')
    return {
        'os': platform.platform(), 'python': platform.python_version(),
        'python_build_platform': sysconfig.get_platform(),
        'windows_architecture': native_windows_architecture(),
        'current_windows_account': current_account(),
        'storage': {drive: {'free_gib': round(shutil.disk_usage(drive).free / 2**30, 1)} for drive in ['C:/', 'D:/']},
        'reference_folder': {'path': str(reference), 'exists': reference.is_dir(), 'content_read': False, 'writes': False},
        'ollama_models_environment': os.environ.get('OLLAMA_MODELS'),
        'account_discovery_scope': 'Current Windows identity only. Email, browser sessions, tokens and saved passwords are not inspected.',
        'service_accounts': 'Not linked. Each service requires its official sign-in flow.',
        'camera_frames_collected': False,
    }
