"""Desktop view of recorded task events and actual local voice-service state."""
import ctypes
import datetime as dt
import json
import math
from pathlib import Path
import shutil
import subprocess
import tkinter as tk

ROOT=Path(__file__).resolve().parent
PYTHON=Path('D:/X-System/runtime/x-personal-venv/Scripts/python.exe')
BG='#0c1322'; PANEL='#142139'; FG='#e5edf8'; MUTED='#a5b8d1'; CYAN='#52d7ed'; GREEN='#7ee5ae'; AMBER='#ffd186'


def read_json(path):
    try:return json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError,ValueError):return {}


def alive(pid):
    if not pid:return False
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32]
    kernel.OpenProcess.restype=ctypes.c_void_p
    kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)]
    kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=kernel.OpenProcess(0x1000,False,int(pid))
    if not handle:return False
    try:
        code=ctypes.c_uint32()
        return bool(kernel.GetExitCodeProcess(handle,ctypes.byref(code))) and code.value==259
    finally:kernel.CloseHandle(handle)


class Board:
    def __init__(self):
        self.root=tk.Tk();self.root.title('X Live — متابعة الشغل');self.root.geometry('1100x760');self.root.minsize(820,640)
        self.root.configure(bg=BG)
        tk.Label(self.root,text='X  /  LIVE',font=('Segoe UI',23,'bold'),bg=BG,fg=CYAN).pack(anchor='w',padx=26,pady=(16,0))
        tk.Label(self.root,text='لوحة متابعة التنفيذ ومحرك الصوت',font=('Segoe UI',20,'bold'),bg=BG,fg=FG).pack(anchor='e',padx=26)
        self.updated=tk.Label(self.root,bg=BG,fg=MUTED,font=('Segoe UI',11));self.updated.pack(anchor='e',padx=26)
        self.canvas=tk.Canvas(self.root,height=150,bg=BG,highlightthickness=0);self.canvas.pack(fill='x',padx=24)
        self.status=tk.Label(self.root,bg=PANEL,fg=FG,font=('Segoe UI',15),anchor='e',padx=18,pady=14,wraplength=950)
        self.status.pack(fill='x',padx=26,pady=(0,12))
        self.metrics=tk.Label(self.root,bg=BG,fg=GREEN,font=('Segoe UI',12),anchor='e');self.metrics.pack(fill='x',padx=26)
        controls=tk.Frame(self.root,bg=BG);controls.pack(fill='x',padx=26,pady=12)
        self.button(controls,'تجربة صوت X',lambda:self.run('speak')).pack(side='right',padx=5)
        self.button(controls,'فحص الجاهزية',lambda:self.run('doctor')).pack(side='right',padx=5)
        self.button(controls,'فتح المشروع في VS Code',self.open_code).pack(side='right',padx=5)
        self.button(controls,'فتح مجلد X',lambda:subprocess.Popen(['explorer.exe',str(ROOT)])).pack(side='right',padx=5)
        self.button(controls,'إيقاف محرك حسن',lambda:self.run('voice-stop')).pack(side='right',padx=5)
        chat_controls=tk.Frame(self.root,bg=BG);chat_controls.pack(fill='x',padx=26,pady=(0,6))
        self.button(chat_controls,'محادثة مع X بالكتابة',lambda:self.run('chat','--text')).pack(side='right',padx=5)
        self.button(chat_controls,'حالة عقل X',lambda:self.run('mind-status')).pack(side='right',padx=5)
        self.button(chat_controls,'بحث X على الإنترنت',lambda:self.run('research')).pack(side='right',padx=5)
        self.button(chat_controls,'تنفيذ مهمة بحث',lambda:self.run('workflow')).pack(side='right',padx=5)
        self.button(chat_controls,'محادثة مع X بالصوت',lambda:self.run('chat')).pack(side='right',padx=5)
        tk.Label(self.root,text='آخر إجراءات مسجلة',font=('Segoe UI',13,'bold'),bg=BG,fg=FG).pack(anchor='e',padx=26)
        self.events=tk.Text(self.root,height=7,bg=PANEL,fg=FG,font=('Segoe UI',11),relief='flat',wrap='word',padx=14,pady=10)
        self.events.tag_configure('rtl',justify='right');self.events.pack(fill='both',expand=True,padx=26,pady=6)
        tk.Label(self.root,text='سجل تشغيل محرك الصوت',font=('Segoe UI',12),bg=BG,fg=MUTED).pack(anchor='e',padx=26)
        self.log=tk.Text(self.root,height=5,bg=BG,fg=MUTED,font=('Consolas',9),relief='flat',wrap='word');self.log.pack(fill='x',padx=26,pady=(0,8))
        self.tick=0;self.busy=False;self.phase='idle';self.last_events='';self.last_log=''
        self.refresh();self.animate();self.root.mainloop()

    def button(self,parent,text,command):
        return tk.Button(parent,text=text,command=command,bg=PANEL,fg=FG,activebackground=CYAN,activeforeground=BG,
                         font=('Segoe UI',10),relief='flat',padx=12,pady=8,cursor='hand2')

    def run(self,action,*extra):
        # Interactive console lets the user complete Hello and read the result.
        subprocess.Popen(['cmd.exe','/k',str(ROOT/'X.cmd'),action,*extra],cwd=ROOT,creationflags=subprocess.CREATE_NEW_CONSOLE)

    def open_code(self):
        candidates=[Path('D:/Microsoft VS Code/Code.exe'),Path.home()/'AppData/Local/Programs/Microsoft VS Code/Code.exe']
        executable=next((str(p) for p in candidates if p.is_file()),None) or shutil.which('code')
        if executable:
            subprocess.Popen([executable,str(ROOT)],cwd=ROOT)
        else:
            from tkinter import messagebox
            messagebox.showinfo('VS Code','لم أعثر على مشغل VS Code. يمكنك فتح المجلد من البرنامج مباشرة.')

    def refresh(self):
        activity=read_json(ROOT/'live-activity.json')
        runtime=read_json(ROOT/'voice-runtime.json')
        self.agents=read_json(ROOT/'agents-live.json')
        active=alive(runtime.get('pid'))
        ready=False
        if active:
            try:
                from x_personal.voicetut_speech import request
                ready=json.loads(request('/health',timeout=.15)).get('ready',False)
            except Exception:pass
        self.phase='ready' if ready else ('loading' if active else 'stopped')
        try:
            age=max(0,int((dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(activity['at'])).total_seconds()))
        except (ValueError,KeyError):age=None
        generating=active and runtime.get('stage')=='generating'
        self.busy=generating or active and not ready or (activity.get('state')=='running' and age is not None and age<90)
        message=activity.get('message','لا توجد مهمة مسجلة بعد')
        if age is not None and age>90 and activity.get('state')=='running':message+=' — الحالة المسجلة قديمة، في انتظار تحديث'
        self.status.config(text=message)
        state='يولّد الصوت الآن' if generating else ('المحرك محمّل' if ready else ('عملية التشغيل موجودة، لم تعلن الجاهزية بعد' if active else 'متوقف'))
        self.metrics.config(text='صوت حسن: '+state,fg=GREEN if ready else AMBER)
        now=dt.datetime.now().strftime('%H:%M:%S')
        self.updated.config(text=f'فحص محلي: {now}  •  عمر آخر إجراء مسجل: {age if age is not None else "—"} ثانية')
        rendered='\n\n'.join(e['message'] for e in activity.get('events',[])[-7:][::-1])
        if rendered!=self.last_events:
            self.events.config(state='normal');self.events.delete('1.0','end');self.events.insert('end',rendered,'rtl');self.events.config(state='disabled');self.last_events=rendered
        try:
            path=ROOT/'voicetut-service.log'
            with path.open('rb') as stream:
                stream.seek(max(0,path.stat().st_size-4000));tail=stream.read().decode('utf-8',errors='replace')
            tail='\n'.join(tail.splitlines()[-9:])
        except OSError:tail='لم يبدأ سجل محرك الصوت بعد.'
        if tail!=self.last_log:
            self.log.config(state='normal');self.log.delete('1.0','end');self.log.insert('end',tail);self.log.config(state='disabled');self.last_log=tail
        self.root.after(1500,self.refresh)

    def animate(self):
        self.tick+=1;self.canvas.delete('all')
        width=max(700,self.canvas.winfo_width());cx=width/2;cy=65
        agents=getattr(self,'agents',{}).get('agents',[])
        if not agents:
            self.canvas.create_text(cx,cy,text='في انتظار رصد الوكلاء الفعليين',fill=MUTED,font=('Segoe UI',14))
        for i,agent in enumerate(agents):
            x=(i+1)*width/(len(agents)+1)
            name=agent.get('display_name',agent.get('id','وكيل'))
            color=CYAN if self.busy else (GREEN if self.phase=='ready' else MUTED)
            radius=28+(2*math.sin(self.tick/8+i) if self.busy else 0)
            self.canvas.create_oval(x-radius,cy-radius,x+radius,cy+radius,outline=color,width=2)
            self.canvas.create_text(x,cy,text='AI',fill=FG,font=('Segoe UI',13,'bold'))
            self.canvas.create_text(x,cy+45,text=name,fill=FG,font=('Segoe UI',12,'bold'))
            self.canvas.create_text(x,cy+69,text=agent.get('role',''),fill=MUTED,font=('Segoe UI',10))
        self.canvas.create_text(width-4,12,anchor='e',text='الوكلاء الفعليون • آخر رصد: '+getattr(self,'agents',{}).get('observed_at','غير متاح'),fill=MUTED,font=('Segoe UI',9))
        self.root.after(45,self.animate)


if __name__=='__main__':Board()
