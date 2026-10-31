"""Open official account sites in a dedicated, persistent X browser profile.

Logging in establishes a browser session only; it does not grant X API access.
No passwords, cookies, or tokens are extracted by this launcher.
"""
from pathlib import Path
import subprocess
import tkinter as tk

SITES = [
    ('WhatsApp Business', 'https://web.whatsapp.com/'),
    ('Meta Business — Facebook / Instagram', 'https://business.facebook.com/'),
    ('Instagram', 'https://www.instagram.com/'),
    ('TikTok', 'https://www.tiktok.com/login'),
    ('Property Finder Expert', 'https://expert.propertyfinder.ae/'),
    ('Yahoo Mail', 'https://mail.yahoo.com/'),
    ('Gmail', 'https://mail.google.com/'),
    ('Outlook', 'https://outlook.office.com/mail/'),
]
EDGE = next((p for p in [Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'), Path('C:/Program Files/Microsoft/Edge/Application/msedge.exe')] if p.exists()), None)
PROFILE = Path('D:/X-System/runtime/x-work-browser')

def open_site(url):
    if EDGE is None:
        status.config(text='Microsoft Edge غير موجود — لم يتم فتح الحساب')
        return
    PROFILE.mkdir(parents=True, exist_ok=True)
    subprocess.Popen([str(EDGE), '--user-data-dir=' + str(PROFILE), '--no-first-run', url])
    status.config(text='سجّل الدخول بنفسك في المتصفح. حالة الربط مع X لم تُختبر بعد.')

if __name__ == '__main__':
    root = tk.Tk()
    root.title('X — حسابات الشغل')
    root.geometry('650x650')
    root.configure(bg='#0c1322')
    tk.Label(root, text='X — تسجيل دخول حسابات الشغل', bg='#0c1322', fg='#52d7ed', font=('Segoe UI', 19)).pack(pady=18)
    tk.Label(root, text='اختار خدمة وسجّل الدخول في صفحتها الرسمية\nالجلسات محفوظة في متصفح منفصل للشغل على الجهاز', bg='#0c1322', fg='white', font=('Segoe UI', 12)).pack(pady=8)
    for name, url in SITES:
        tk.Button(root, text=name, command=lambda u=url: open_site(u), bg='#142139', fg='white', font=('Segoe UI', 12), width=43).pack(pady=5)
    status = tk.Label(root, text='تسجيل الدخول وحده لا يفعّل إدارة الحسابات تلقائيًا', bg='#0c1322', fg='#ffd186', wraplength=590, font=('Segoe UI', 11))
    status.pack(pady=18)
    root.after(600, lambda: open_site(SITES[0][1]))
    root.mainloop()
