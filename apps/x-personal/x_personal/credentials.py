"""Read and write X's per-user Windows Credential Manager secrets."""
import ctypes
import os
from ctypes import wintypes

_TARGET = 'X-System/Gemini-API-Key'
_CRED_TYPE_GENERIC = 1
_CRED_PERSIST_LOCAL_MACHINE = 2


class _Credential(ctypes.Structure):
    _fields_ = [
        ('Flags', wintypes.DWORD),
        ('Type', wintypes.DWORD),
        ('TargetName', wintypes.LPWSTR),
        ('Comment', wintypes.LPWSTR),
        ('LastWritten', wintypes.FILETIME),
        ('CredentialBlobSize', wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)),
        ('Persist', wintypes.DWORD),
        ('AttributeCount', wintypes.DWORD),
        ('Attributes', ctypes.c_void_p),
        ('TargetAlias', wintypes.LPWSTR),
        ('UserName', wintypes.LPWSTR),
    ]


def read_gemini_api_key():
    if os.name != 'nt':
        return None
    advapi32 = ctypes.WinDLL('Advapi32', use_last_error=True)
    advapi32.CredReadW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.POINTER(_Credential)),
    ]
    advapi32.CredReadW.restype = wintypes.BOOL
    advapi32.CredFree.argtypes = [ctypes.c_void_p]
    credential = ctypes.POINTER(_Credential)()
    if not advapi32.CredReadW(
        _TARGET, _CRED_TYPE_GENERIC, 0, ctypes.byref(credential)
    ):
        error = ctypes.get_last_error()
        if error == 1168:
            return None
        raise ctypes.WinError(error)
    try:
        blob = credential.contents
        return ctypes.string_at(
            blob.CredentialBlob, blob.CredentialBlobSize
        ).decode('utf-8')
    finally:
        advapi32.CredFree(credential)


def store_gemini_api_key(api_key):
    if os.name != 'nt':
        raise RuntimeError('Gemini API key storage requires Windows.')
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError('Gemini API key cannot be empty.')
    secret = api_key.strip().encode('utf-8')
    if len(secret) > 2560:
        raise ValueError('Gemini API key is too long.')
    secret_buffer = (ctypes.c_ubyte * len(secret)).from_buffer_copy(secret)
    credential = _Credential(
        0,
        _CRED_TYPE_GENERIC,
        _TARGET,
        None,
        wintypes.FILETIME(0, 0),
        len(secret),
        secret_buffer,
        _CRED_PERSIST_LOCAL_MACHINE,
        0,
        None,
        None,
        'X Gemini API',
    )
    advapi32 = ctypes.WinDLL('Advapi32', use_last_error=True)
    advapi32.CredWriteW.argtypes = [
        ctypes.POINTER(_Credential),
        wintypes.DWORD,
    ]
    advapi32.CredWriteW.restype = wintypes.BOOL
    if not advapi32.CredWriteW(ctypes.byref(credential), 0):
        raise ctypes.WinError(ctypes.get_last_error())
