"""Windows Hello desktop interop. Never reads biometrics or accepts a camera match.

Uses IUserConsentVerifierInterop with an HWND, not the UWP-only request method.
WinRT COM calls are kept on one thread; all references are released.
"""
import ctypes as C
import time
import uuid
from contextlib import contextmanager
from ctypes import wintypes as W

PTR = C.c_void_p
HRESULT = C.c_int32


class GUID(C.Structure):
    _fields_ = [('data', C.c_ubyte * 16)]

    @classmethod
    def parse(cls, text):
        return cls((C.c_ubyte * 16).from_buffer_copy(uuid.UUID(text).bytes_le))


def check(hr):
    if hr < 0:
        raise OSError(f'Windows API failed: 0x{hr & 0xffffffff:08X}')


def method(obj, slot, result, *types):
    table = C.cast(obj, C.POINTER(C.POINTER(PTR))).contents
    return C.WINFUNCTYPE(result, PTR, *types)(table[slot])


def release(obj):
    if obj:
        method(obj, 2, C.c_uint32)(obj)


def query(obj, iid):
    result = PTR()
    guid = GUID.parse(iid)
    check(method(obj, 0, HRESULT, C.POINTER(GUID), C.POINTER(PTR))(obj, C.byref(guid), C.byref(result)))
    return result


class Runtime:
    def __init__(self, apartment=1):
        self.api = C.WinDLL('combase')
        self.api.RoInitialize.argtypes = [C.c_uint32]
        self.api.RoInitialize.restype = HRESULT
        self.api.RoUninitialize.argtypes = []
        self.api.RoUninitialize.restype = None
        self.api.WindowsCreateString.argtypes = [W.LPCWSTR, C.c_uint32, C.POINTER(PTR)]
        self.api.WindowsCreateString.restype = HRESULT
        self.api.WindowsDeleteString.argtypes = [PTR]
        self.api.WindowsDeleteString.restype = HRESULT
        self.api.RoGetActivationFactory.argtypes = [PTR, C.POINTER(GUID), C.POINTER(PTR)]
        self.api.RoGetActivationFactory.restype = HRESULT
        hr = self.api.RoInitialize(apartment)
        self.initialized = hr >= 0
        if hr < 0 and (hr & 0xffffffff) != 0x80010106:
            check(hr)

    @contextmanager
    def string(self, text):
        handle = PTR()
        # Windows counts UTF-16 code units, not Unicode code points.
        check(self.api.WindowsCreateString(text, len(text.encode('utf-16-le')) // 2, C.byref(handle)))
        try:
            yield handle
        finally:
            self.api.WindowsDeleteString(handle)

    def factory(self, iid):
        result = PTR()
        guid = GUID.parse(iid)
        with self.string('Windows.Security.Credentials.UI.UserConsentVerifier') as name:
            check(self.api.RoGetActivationFactory(name, C.byref(guid), C.byref(result)))
        return result

    def close(self):
        if self.initialized:
            self.api.RoUninitialize()
            self.initialized = False


def await_enum(operation, timeout=90, pump=None):
    info = query(operation, '00000036-0000-0000-c000-000000000046')
    try:
        deadline = time.monotonic() + timeout
        while True:
            status = C.c_int32()
            check(method(info, 7, HRESULT, C.POINTER(C.c_int32))(info, C.byref(status)))
            if status.value == 1:
                result = C.c_int32()
                check(method(operation, 8, HRESULT, C.POINTER(C.c_int32))(operation, C.byref(result)))
                return result.value
            if status.value != 0:
                raise PermissionError('Windows verification canceled or failed.')
            if time.monotonic() >= deadline:
                method(info, 9, HRESULT)(info)  # IAsyncInfo.Cancel
                raise TimeoutError('Windows verification timed out.')
            if pump:
                pump()
            time.sleep(0.03)
    finally:
        # Close only after completion; Cancel may still be completing on timeout.
        release(info)


def availability():
    runtime = Runtime()
    factory = operation = None
    try:
        factory = runtime.factory('af4f3f91-564c-4ddc-b8b5-973447627c65')
        operation = PTR()
        check(method(factory, 6, HRESULT, C.POINTER(PTR))(factory, C.byref(operation)))
        code = await_enum(operation, timeout=15)
        names = ['available', 'device_not_present', 'not_configured', 'disabled_by_policy', 'device_busy']
        return {'code': code, 'status': names[code] if 0 <= code < len(names) else 'unknown'}
    finally:
        release(operation)
        release(factory)
        runtime.close()


def verify(message='X: verify the current Windows account to continue.'):
    import tkinter as tk
    if availability()['code'] != 0:
        raise PermissionError('Windows Hello is unavailable. Configure sign-in options first.')
    root = tk.Tk()
    root.title('X — Windows verification')
    root.geometry('440x140')
    tk.Label(root, text='X — تأكيد حساب Windows\nأكمل التحقق في نافذة أمان Windows', pady=20).pack()
    closed = False

    def cancel():
        nonlocal closed
        closed = True

    root.protocol('WM_DELETE_WINDOW', cancel)
    root.update()
    user32 = C.WinDLL('user32')
    user32.GetAncestor.argtypes = [W.HWND, C.c_uint]
    user32.GetAncestor.restype = W.HWND
    hwnd = user32.GetAncestor(root.winfo_id(), 2)
    runtime = Runtime(apartment=0)
    factory = operation = None
    try:
        factory = runtime.factory('39e050c3-4e74-441a-8dc0-b81104df949c')
        signature = ('pinterface({9fc2b0bb-e446-44e2-aa61-9cab8f636af2};'
                     'enum(Windows.Security.Credentials.UI.UserConsentVerificationResult;i4))')
        iid = GUID.parse(str(uuid.uuid5(uuid.UUID('11f47ad5-7b73-42c0-abae-878b1e16adee'), signature)))
        operation = PTR()
        with runtime.string(message) as hmessage:
            check(method(factory, 6, HRESULT, W.HWND, PTR, C.POINTER(GUID), C.POINTER(PTR))(
                factory, hwnd, hmessage, C.byref(iid), C.byref(operation)))

        def pump():
            root.update()
            if closed:
                info = query(operation, '00000036-0000-0000-c000-000000000046')
                try:
                    method(info, 9, HRESULT)(info)
                finally:
                    release(info)
                raise PermissionError('Verification window closed.')

        result = await_enum(operation, pump=pump)
        if result != 0:
            raise PermissionError(f'Windows Hello did not verify the user (result={result}).')
        return True
    finally:
        release(operation)
        release(factory)
        runtime.close()
        root.destroy()
