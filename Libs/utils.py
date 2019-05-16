# from SFmpq import *

from Tkinter import *
from tkMessageBox import askquestion,OK
import tkFileDialog
from textwrap import wrap
import os,re,webbrowser,sys,traceback,urllib,errno,tempfile,codecs,copy,platform
win_reg = True
try:
	from _winreg import *
except:
	win_reg = False

if hasattr(sys, 'frozen'):
	BASE_DIR = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
else:
	BASE_DIR = os.path.dirname(os.path.dirname(unicode(__file__, sys.getfilesystemencoding())))
if os.path.exists(BASE_DIR):
	os.chdir(BASE_DIR)

import json
with open(os.path.join(BASE_DIR, 'Libs', 'versions.json'), 'r') as f:
	VERSIONS = json.load(f)

couriernew = ('Courier', -12, 'normal')
couriersmall = ('Courier', -8, 'normal')
ARROW = None
TRANS_FIX = None

def is_windows():
	return (platform.system().lower() == 'windows')
def is_mac():
	return (platform.system().lower() == 'darwin')

def startup(toplevel):
	toplevel.lift()
	toplevel.call('wm', 'attributes', '.', '-topmost', True)
	toplevel.after_idle(toplevel.call, 'wm', 'attributes', '.', '-topmost', False)
	toplevel.focus_force()
	try:
		from Cocoa import NSRunningApplication, NSApplicationActivateIgnoringOtherApps

		app = NSRunningApplication.runningApplicationWithProcessIdentifier_(os.getpid())
		app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
	except:
		pass
	toplevel.mainloop()

# Decorator
def debug_func_log(should_log_call=None):
	def decorator(func):
		def do_log(*args, **kwargs):
			import uuid
			ref = uuid.uuid4().hex
			log = not should_log_call or should_log_call(func, args, kwargs)
			if log:
				print "Func  : %s (%s)" % (func.__name__, ref)
				print "\tArgs  : %s" % (args,)
				print "\tkwargs: %s" % kwargs
			result = func(*args, **kwargs)
			if log:
				print "Func  : %s (%s)" % (func.__name__, ref)
				print "\tResult: %s" % (result,)
			return result
		return do_log
	return decorator
def debug_state(states, history=[]):
	n = len(history)
	print '##### %d: %s' % (n, states[n] if n < len(states) else 'Unknown')
	history.append(None)

def parse_geometry(geometry):
	match = re.match(r'(?:(\d+)x(\d+))?\+(-?\d+)\+(-?\d+)(\^)?',geometry)
	return tuple(None if v == None else int(v) for v in match.groups()[:-1]) + (True if match.group(5) else False,)

def parse_scrollregion(scrollregion):
	return tuple(int(v) for v in scrollregion.split(' '))

def isstr(s):
	return isinstance(s,str) or isinstance(s,unicode)

def nearest_multiple(v, m, r=round):
	return m * int(r(v / float(m)))

def register_registry(prog,type,filetype,progpath,icon):
	if not win_reg:
		raise PyMSError('Registry', 'You can currently only set as the default program on Windows machines.')
	def delkey(key,sub_key):
		try:
			h = OpenKey(key,sub_key)
		except WindowsError, e:
			if e.errno == 2:
				return
			raise
		except:
			raise
		try:
			while True:
				n = EnumKey(h,0)
				delkey(h,n)
		except EnvironmentError:
			pass
		h.Close()
		DeleteKey(key,sub_key)

	key = '%s:%s' % (prog,filetype)
	try:
		delkey(HKEY_CLASSES_ROOT, '.' + filetype)
		delkey(HKEY_CLASSES_ROOT, key)
		SetValue(HKEY_CLASSES_ROOT, '.' + filetype, REG_SZ, key)
		SetValue(HKEY_CLASSES_ROOT, key, REG_SZ, 'StarCraft %s *.%s file (%s)' % (type,filetype,prog))
		SetValue(HKEY_CLASSES_ROOT, key + '\\DefaultIcon', REG_SZ, icon)
		SetValue(HKEY_CLASSES_ROOT, key + '\\Shell', REG_SZ, 'open')
		SetValue(HKEY_CLASSES_ROOT, key + '\\Shell\\open\\command', REG_SZ, '"%s" "%s" --gui "%%1"' % (sys.executable.replace('python.exe','pythonw.exe'),progpath))
	except:
		raise PyMSError('Registry', 'Could not complete file association.',exception=sys.exc_info())
	askquestion(title='Success!', message='The file association was set.', type=OK)

def flags(value, length):
	if isstr(value):
		if len(value) != length or value.replace('0','').replace('1',''):
			raise
		return sum(int(x)*(2**n) for n,x in enumerate(reversed(value)))
	return ''.join(reversed([str(value/(2**n)%2) for n in range(length)]))

def ccopy(lst):
	r = []
	for item in lst:
		if isinstance(item, list):
			r.append(ccopy(item))
		else:
			r.append(item)
	return r

def fit(label, text, width=80, end=False, indent=0):
	r = label
	if not indent:
		s = len(r)
	else:
		s = indent
	indent = False
	for p in text.split('\n'):
		if p:
			for l in wrap(p, width - s):
				if indent:
					r += ' ' * s
				else:
					indent = True
				r += l
				r += '\n'
	return r.rstrip('\n') + ('\n' if end else '')

def removedir(path):
	if os.path.exists(path):
		for r,ds,fs in os.walk(path, topdown=False):
			for f in fs:
				os.remove(os.path.join(r, f))
			for d in ds:
				p = os.path.join(r, d)
				removedir(p)
				os.rmdir(p)
		os.rmdir(path)

class DependencyError(Tk):
	def __init__(self, prog, msg, hotlink=None):
		#Window
		Tk.__init__(self)
		self.resizable(False,False)
		self.title('Dependency Error')
		try:
			self.icon = os.path.join(BASE_DIR,'Images','%s.ico' % prog)
			self.wm_iconbitmap(self.icon)
		except:
			self.icon = '@%s' % os.path.join(BASE_DIR, 'Images','%s.xbm' % prog)
			self.wm_iconbitmap(self.icon)
		Label(self, text=msg, anchor=W, justify=LEFT).pack(side=TOP,pady=2,padx=2)
		if hotlink:
			f = Frame(self)
			Hotlink(f, *hotlink).pack(side=RIGHT, padx=10, pady=2)
			f.pack(side=TOP,fill=X)
		Button(self, text='Ok', width=10, command=self.destroy).pack(side=TOP, pady=2)
		self.update_idletasks()
		w,h = self.winfo_width(),self.winfo_height()
		self.geometry('%ix%i+%i+%i' % (w,h,(self.winfo_screenwidth() - w)/2,(self.winfo_screenheight() - h)/2))

class PyMSError(Exception):
	def __init__(self, type, error, line=None, code=None, warnings=[], exception=None):
		self.type = type
		self.error = error
		self.line = line
		if self.line != None:
			self.line += 1
		self.code = code
		self.warnings = warnings
		self.exception = exception

	def repr(self):
		r = '%s Error: %s' % (self.type, self.error)
		if self.line:
			r += '\n    Line %s: %s' % (self.line, self.code)
		return r

	def __repr__(self):
		r = fit('%s Error: ' % self.type, self.error)
		if self.line:
			r += fit('    Line %s: ' % self.line, self.code)
		if self.warnings:
			for w in self.warnings:
				r += repr(w)
		return r[:-1]

	def __str__(self):
		return repr(self)

class PyMSWarning(Exception):
	def __init__(self, type, warning, line=None, code=None, extra=None, level=0, id=None, sub_warnings=None):
		self.type = type
		self.warning = warning
		self.line = line
		if self.line != None:
			self.line += 1
		self.code = code
		self.extra = extra
		self.level = level
		self.id = id
		self.sub_warnings = [] if not sub_warnings else sub_warnings

	def repr(self):
		r = fit('%s Warning%s: ' % (self.type, ' (%s)' % self.id if self.id else ''), self.warning, end=True)
		if self.line:
			r += fit('    Line %s: ' % self.line, self.code, end=True)
		for w in self.sub_warnings:
			r += w.repr()
		return r

	def __repr__(self):
		r = fit('%s Warning%s: ' % (self.type, ' (%s)' % self.id if self.id else ''), self.warning)
		if self.line:
			r += fit('    Line %s: ' % self.line, self.code)
		for w in self.sub_warnings:
			r += repr(w)
		return r[:-1]

class PyMSWarnList(Exception):
	def __init__(self, warnings):
		self.warnings = warnings

	def __repr__(self):
		r = ''
		for w in self.warnings:
			r += repr(w)
		return r[:-1]

class PyMSDialog(Toplevel):
	def __init__(self, parent, title, center=True, grabwait=True, hidden=False, escape=False, resizable=(True,True), set_min_size=(False,False)):
		Toplevel.__init__(self, parent)
		self.title(title)
		self.icon = parent.icon
		self.wm_iconbitmap(parent.icon)
		self.protocol('WM_DELETE_WINDOW', self.cancel)
		if escape:
			self.bind('<Escape>', self.cancel)
		#self.transient(parent)
		self.parent = parent
		focus = self.widgetize()
		self.update_idletasks()
		if not focus:
			focus = self
		focus.focus_set()
		w,h,x,y,fullscreen = parse_geometry(self.winfo_geometry())
		screen_w = self.winfo_screenwidth()
		screen_h = self.winfo_screenheight()
		if center:
			self.geometry('+%d+%d' % ((screen_w-w)/2,(screen_h-h)/2))
		self.resizable(*resizable)
		min_w = 0
		max_w = screen_w
		min_h = 0
		max_h = screen_h
		if not resizable[0]:
			min_w = max_w = w
		elif set_min_size[0]:
			min_w = w
		if not resizable[1]:
			min_h = max_h = h
		elif set_min_size[1]:
			min_h = h
		self.minsize(min_w, min_h)
		self.maxsize(max_w, max_h)
		self.setup_complete()
		if grabwait:
			self.grab_wait()

	def grab_wait(self):
			self.grab_set()
			self.wait_window(self)

	def widgetize(self):
		pass
	def setup_complete(self):
		pass

	def dismiss(self):
		self.withdraw()
		self.update_idletasks()
		self.parent.focus_set()
		self.destroy()

	def ok(self, event=None):
		self.dismiss()

	def cancel(self, event=None):
		self.dismiss()

class InternalErrorDialog(PyMSDialog):
	CAPTURE_NONE = 0
	CAPTURE_PRINT = 1
	CAPTURE_DIALOG = 2
	@staticmethod
	def capture(parent, prog, debug=0):
		trace = ''.join(traceback.format_exception(*sys.exc_info()))
		if debug == InternalErrorDialog.CAPTURE_DIALOG:
			InternalErrorDialog(parent, prog, txt=trace)
		elif debug == InternalErrorDialog.CAPTURE_PRINT:
			print trace

	def __init__(self, parent, prog, handler=None, txt=None):
		self.prog = prog
		self.handler = handler
		self.txt = txt
		PyMSDialog.__init__(self, parent, 'PyMS Internal Error!', grabwait=True)

	def widgetize(self):
		self.bind('<Control-a>', self.selectall)
		Label(self, text='The PyMS program "%s" has encountered an unknown internal error.\nThe program will attempt to continue, but may cause problems or crash once you press Ok.\nPlease contact poiuy_qwert and send him this traceback with any relivant information.' % self.prog, justify=LEFT).pack(side=TOP, padx=2, pady=2, fill=X)
		r = Frame(self)
		Hotlink(r, 'Contact', self.contact).pack(side=RIGHT, padx=10, pady=2)
		r.pack(fill=X)
		frame = Frame(self, bd=2, relief=SUNKEN)
		hscroll = Scrollbar(frame, orient=HORIZONTAL)
		vscroll = Scrollbar(frame)
		self.text = Text(frame, bd=0, highlightthickness=0, width=70, height=10, xscrollcommand=hscroll.set, yscrollcommand=vscroll.set, wrap=NONE, exportselection=0, state=DISABLED)
		if self.txt:
			self.text['state'] = NORMAL
			self.text.insert(END, self.txt)
			self.text['state'] = DISABLED
		self.text.grid(sticky=NSEW)
		hscroll.config(command=self.text.xview)
		hscroll.grid(sticky=EW)
		vscroll.config(command=self.text.yview)
		vscroll.grid(sticky=NS, row=0, column=1)
		frame.grid_rowconfigure(0, weight=1)
		frame.grid_columnconfigure(0, weight=1)
		frame.pack(fill=BOTH, pady=2, padx=2, expand=1)
		buttonbar = Frame(self)
		ok = Button(buttonbar, text='Ok', width=10, command=self.ok)
		ok.pack(side=LEFT, padx=3)
		buttonbar.pack(side=BOTTOM, pady=10)
		return ok

	def selectall(self, key=None):
		self.text.focus_set()
		self.text.tag_add(SEL, 1.0, END)

	def cancel(self):
		if self.handler:
			self.handler.clear_window()
		PyMSDialog.cancel(self)
	def ok(self):
		if self.handler:
			self.handler.clear_window()
		PyMSDialog.ok(self)

	def contact(self, e=None):
		webbrowser.open(os.path.join(os.path.dirname(BASE_DIR), 'Docs', 'intro.html'))

	def add_text(self, text):
		self.text['state'] = NORMAL
		self.text.insert(END, text)
		self.text['state'] = DISABLED

class ErrorDialog(PyMSDialog):
	def __init__(self, parent, error):
		self.error = error
		PyMSDialog.__init__(self, parent, '%s Error!' % error.type, resizable=(False, False))

	def widgetize(self):
		Label(self, justify=LEFT, anchor=W, text=self.error.repr(), wraplen=640).pack(pady=10, padx=5)
		frame = Frame(self)
		ok = Button(frame, text='Ok', width=10, command=self.ok)
		ok.pack(side=LEFT, padx=3)
		w = len(self.error.warnings)
		p = 's'
		if w == 1:
			p = ''
		Button(frame, text='%s Warning%s' % (w, p), width=10, command=self.viewwarnings, state=[NORMAL,DISABLED][not self.error.warnings]).pack(side=LEFT, padx=3)
		Button(frame, text='Copy', width=10, command=self.copy).pack(side=LEFT, padx=6)
		if self.error.exception:
			Button(frame, text='Internal Error', width=10, command=self.internal).pack(side=LEFT, padx=6)
		frame.pack(pady=10)
		return ok

	def copy(self):
		self.clipboard_clear()
		self.clipboard_append(self.error.repr())

	def viewwarnings(self):
		WarningDialog(self, self.error.warnings)

	def internal(self):
		InternalErrorDialog(self, sys.stderr.prog, txt=''.join(traceback.format_exception(*self.error.exception)))

class WarningDialog(PyMSDialog):
	def __init__(self, parent, warnings, cont=False):
		self.warnings = warnings
		self.cont = cont
		PyMSDialog.__init__(self, parent, 'Warning!', resizable=(False, False))

	def widgetize(self):
		self.bind('<Control-a>', self.selectall)
		frame = Frame(self, bd=2, relief=SUNKEN)
		hscroll = Scrollbar(frame, orient=HORIZONTAL)
		vscroll = Scrollbar(frame)
		self.warntext = Text(frame, bd=0, highlightthickness=0, width=60, height=10, xscrollcommand=hscroll.set, yscrollcommand=vscroll.set, wrap=NONE, exportselection=0)
		self.warntext.tag_config('highlevel', foreground='#960000')
		self.warntext.grid()
		hscroll.config(command=self.warntext.xview)
		hscroll.grid(sticky=EW)
		vscroll.config(command=self.warntext.yview)
		vscroll.grid(sticky=NS, row=0, column=1)
		for warning in self.warnings:
			if warning.level:
				self.warntext.insert(END, warning.repr(), 'highlevel')
			else:
				self.warntext.insert(END, warning.repr())
		self.warntext['state'] = DISABLED
		frame.pack(side=TOP, pady=2, padx=2)
		buttonbar = Frame(self)
		ok = Button(buttonbar, text='Ok', width=10, command=self.ok)
		ok.pack(side=LEFT, padx=3)
		if self.cont:
			Button(buttonbar, text='Cancel', width=10, command=self.cancel).pack(side=LEFT)
		buttonbar.pack(pady=10)
		return ok

	def selectall(self, key=None):
		self.warntext.focus_set()
		self.warntext.tag_add(SEL, 1.0, END)

	def ok(self):
		self.cont = True
		PyMSDialog.ok(self)

	def cancel(self):
		self.cont = False
		PyMSDialog.ok(self)

class WarnDialog(PyMSDialog):
	def __init__(self, parent, message, title='Warning!', show_dont_warn=False):
		self.message = message
		self.dont_warn = IntVar()
		self.show_dont_warn = show_dont_warn
		PyMSDialog.__init__(self, parent, title, resizable=(False, False), set_min_size=(300, 100))

	def widgetize(self):
		Label(self, text=self.message).pack(side=TOP, padx=20,pady=10)
		frame = Frame(self)
		if self.show_dont_warn:
			Checkbutton(frame, text="Don't warn me again", variable=self.dont_warn, anchor=W).pack(side=LEFT, padx=(0,10))
		ok = Button(frame, text='Ok', width=10, command=self.ok)
		ok.pack(side=RIGHT)
		frame.pack(side=BOTTOM, fill=BOTH, padx=20,pady=(0,10))
		return ok

class AboutDialog(PyMSDialog):
	def __init__(self, parent, program, version, thanks=[]):
		self.program = program
		self.version = version
		self.thanks = thanks
		self.thanks.extend([
			('ShadowFlare','For SFmpq, some file specs, and all her tools!'),
			('BroodWarAI.com','Support and hosting of course!'),
			('Blizzard','For creating StarCraft and BroodWar...'),
		])
		PyMSDialog.__init__(self, parent, 'About %s' % program, resizable=(False, False))

	def widgetize(self):
		name = Label(self, text='%s %s' % (self.program, self.version), font=('Courier', 18, 'bold'))
		name.pack()
		frame = Frame(self)
		Label(frame, text='Author:').grid(stick=E)
		Label(frame, text='Homepage:').grid(stick=E)
		Hotlink(frame, 'poiuy_qwert (p.q.poiuy_qwert@gmail.com)', self.author).grid(row=0, column=1, stick=W)
		Hotlink(frame, 'http://www.broodwarai.com/index.php?page=pyms', self.homepage).grid(row=1, column=1, stick=W)
		frame.pack(padx=1, pady=2)
		if self.thanks:
			Label(self, text='Special Thanks To:', font=('Courier', 10, 'bold')).pack(pady=2)
			thanks = Frame(self)
			font = ('Courier', 8, 'bold')
			row = 0
			for who,why in self.thanks:
				if who == 'BroodWarAI.com':
					Hotlink(thanks, who, self.broodwarai, [('Courier', 8, 'bold'),('Courier', 8, 'bold underline')]).grid(sticky=E)
				else:
					Label(thanks, text=who, font=font).grid(stick=E)
				Label(thanks, text=why).grid(row=row, column=1, stick=W)
				row += 1
			thanks.pack(pady=1)
		ok = Button(self, text='Ok', width=10, command=self.ok)
		ok.pack(pady=5)
		return ok

	def author(self, e=None):
		webbrowser.open('mailto:p.q.poiuy.qwert@hotmail.com')

	def homepage(self, e=None):
		webbrowser.open('http://www.broodwarai.com/index.php?page=pyms')

	def broodwarai(self, e=None):
		webbrowser.open('http://www.broodwarai.com')

class Hotlink(Label):
	def __init__(self, parent, text, callback=None, fonts=[('Courier', 8, 'normal'),('Courier', 8, 'underline')]):
		self.fonts = fonts
		Label.__init__(self, parent, text=text, foreground='#0000FF', cursor='hand2', font=fonts[0])
		self.bind('<Enter>', self.enter)
		self.bind('<Leave>', self.leave)
		if callback:
			self.bind('<Button-1>', callback)

	def enter(self, e):
		self['font'] = self.fonts[1]

	def leave(self, e):
		self['font'] = self.fonts[0]

class Notebook(Frame):
	def __init__(self, parent, relief=RAISED, switchcallback=None):
		self.parent = parent
		self.active = None
		self.tab = IntVar()
		self.notebook = Frame(parent)
		self.tabs = Frame(self.notebook)
		self.tabs.pack(fill=X)
		self.pages = {}
		Frame.__init__(self, self.notebook, borderwidth=2, relief=relief)
		Frame.pack(self, fill=BOTH, expand=1)

	def pack(self, **kw):
		self.notebook.pack(kw)

	def grid(self, **kw):
		self.notebook.grid(kw)

	def add_tab(self, fr, title):
		global TRANS_FIX
		if not TRANS_FIX:
			TRANS_FIX = PhotoImage(file=os.path.join(BASE_DIR, 'Images', 'trans_fix.gif'))
		b = Radiobutton(self.tabs, image=TRANS_FIX, text=title, indicatoron=0, compound=RIGHT, variable=self.tab, value=len(self.pages), command=lambda: self.display(title))
		b.pack(side=LEFT)
		self.pages[title] = [fr,len(self.pages)]
		if not self.active:
			self.display(title)
		return b

	def display(self, title):
		if self.active:
			if hasattr(self.active, 'deactivate'):
				self.active.deactivate()
			self.event_generate('<<TabDeactivated>>')
			self.active.forget()
		self.tab.set(self.pages[title][1])
		self.active = self.pages[title][0]
		self.active.pack(fill=BOTH, expand=1, padx=6, pady=6)
		if hasattr(self.active, 'activate'):
			self.active.activate()
		self.event_generate('<<TabActivated>>')

class NotebookTab(Frame):
	def __init__(self, parent):
		self.parent = parent
		Frame.__init__(self, parent)

	def activate(self):
		pass

	def deactivate(self):
		pass

class DropDown(Frame):
	def __init__(self, parent, variable, entries, display=None, width=1, state=NORMAL, stay_right=False, none_name='None', none_value=None):
		self.variable = variable
		self.variable.set = self.set
		self.display = display
		self.stay_right = stay_right
		self._original_display_callback = None
		if display and isinstance(display, Variable):
			self._original_display_callback = display.callback
			def callback_wrapper(num):
				self.set(num)
				if self._original_display_callback:
					self._original_display_callback(self.variable.get())
			display.callback = callback_wrapper
		self.size = min(10,len(entries))
		self.none_name = none_name
		self.none_value = none_value
		Frame.__init__(self, parent, borderwidth=2, relief=SUNKEN)
		self.listbox = Listbox(self, selectmode=SINGLE, font=couriernew, width=width, height=1, borderwidth=0, exportselection=1, activestyle=DOTBOX)
		self.listbox.bind('<Button-1>', self.choose)
		self.listbox.bind('<MouseWheel>', lambda *args: 'break')
		bind = [
			# ('<MouseWheel>', self.scroll),
			('<Home>', lambda a,i=0: self.move(a,i)),
			('<End>', lambda a,i=END: self.move(a,i)),
			('<Up>', lambda a,i=-1: self.move(a,i)),
			('<Left>', lambda a,i=-1: self.move(a,i)),
			('<Down>', lambda a,i=1: self.move(a,i)),
			('<Right>', lambda a,i=-1: self.move(a,i)),
			('<Prior>', lambda a,i=-10: self.move(a,i)),
			('<Next>', lambda a,i=10: self.move(a,i)),
			('<space>', self.choose)
		]
		for b in bind:
			self.bind(*b)
			self.listbox.bind(*b)
		self.setentries(entries)
		self.listbox.pack(side=LEFT, fill=X, expand=1)
		self.listbox['state'] = state
		global ARROW
		if not ARROW:
			ARROW = PhotoImage(file=os.path.join(BASE_DIR, 'Images', 'arrow.gif'))
		self.button = Button(self, image=ARROW, command=self.choose, state=state)
		self.button.image = ARROW
		self.button.pack(side=RIGHT, fill=Y)

	def __setitem__(self, item, value):
		if item == 'state':
			self.listbox['state'] = value
			self.button['state'] = value
		else:
			Frame.__setitem__(self, item, value)

	def setentries(self, entries):
		selected = self.variable.get()
		self.entries = list(entries)
		self.listbox.delete(0,END)
		for entry in entries:
			self.listbox.insert(END, entry)
		if selected >= self.listbox.size():
			selected = self.listbox.size()-1
		self.listbox.see(selected)
		if self.stay_right:
			self.listbox.xview_moveto(1.0)

	def set(self, num):
		self.change(num)
		Variable.set(self.variable, num)
		self.disp(num)
		if self.stay_right:
			self.listbox.xview_moveto(1.0)

	def change(self, num):
		if num >= self.listbox.size():
			num = self.listbox.size()-1
		self.listbox.select_clear(0,END)
		#self.listbox.select_set(num)
		self.listbox.see(num)

	# def scroll(self, e):
	# 	if self.listbox['state'] == NORMAL:
	# 		if e.delta > 0:
	# 			self.move(None, -1)
	# 		elif self.variable.get() < self.listbox.size()-2:
	# 			self.move(None, 1)

	def move(self, e, a):
		if self.listbox['state'] == NORMAL:
			if a not in [0,END]:
				a = max(min(self.listbox.size(),self.variable.get() + a),0)
			self.set(a)
			self.listbox.select_set(a)

	def choose(self, e=None):
		if self.listbox['state'] == NORMAL:
			i = self.variable.get()
			if i == self.none_value:
				n = self.entries.index(self.none_name)
				if n >= 0:
					i = n
			c = DropDownChooser(self, self.entries, i)
			if c.result > -1 and c.result < len(self.entries) and self.entries[c.result] == self.none_name and self.none_value:
				self.set(self.none_value)
			else:
				self.set(c.result)
			self.listbox.select_set(c.result)

	def disp(self, n):
		if self.display:
			if isinstance(self.display, Variable):
				self.display.set(n)
			else:
				self.display(n)

class TextDropDown(Frame):
	def __init__(self, parent, variable, history=[], width=None, state=NORMAL):
		self.variable = variable
		self.set = self.variable.set
		self.history = history
		Frame.__init__(self, parent, borderwidth=2, relief=SUNKEN)
		self.entry = Entry(self, textvariable=self.variable, width=width, bd=0)
		self.entry.pack(side=LEFT, fill=X, expand=1)
		self.entry['state'] = state
		global ARROW
		if not ARROW:
			ARROW = PhotoImage(file=os.path.join(BASE_DIR, 'Images', 'arrow.gif'))
		self.button = Button(self, image=ARROW, command=self.choose, state=state)
		self.button.pack(side=LEFT, fill=Y)

	def focus_set(self, highlight=False):
		self.entry.focus_set()
		if highlight:
			self.entry.selection_range(0,END)

	def __setitem__(self, item, value):
		if item == 'state':
			self.entry['state'] = value
			self.button['state'] = value
		else:
			self.entry[item] = value

	def __getitem__(self, item):
		return self.entry[item]

	def choose(self, e=None):
		if self.entry['state'] == NORMAL and self.history:
			i = -1
			if self.variable.get() in self.history:
				i = self.history.index(self.variable.get())
			c = DropDownChooser(self, self.history, i)
			if c.result > -1:
				self.variable.set(self.history[c.result])

class DropDownChooser(Toplevel):
	def __init__(self, parent, list, select):
		self.focus = 0
		self.parent = parent
		self.result = select
		Toplevel.__init__(self, parent, relief=SOLID, borderwidth=1)
		self.protocol('WM_LOSE_FOCUS', self.select)
		self.wm_overrideredirect(1)
		scrollbar = Scrollbar(self)
		self.listbox = Listbox(self, selectmode=SINGLE, height=min(10,len(list)), borderwidth=0, font=couriernew, highlightthickness=0, yscrollcommand=scrollbar.set, activestyle=DOTBOX)
		for e in list:
			self.listbox.insert(END,e)
		if self.result > -1:
			self.listbox.select_set(self.result)
			self.listbox.see(self.result)
		self.listbox.bind('<ButtonRelease-1>', self.select)
		bind = [
			('<Enter>', lambda e,i=1: self.enter(e,i)),
			('<Leave>', lambda e,i=0: self.enter(e,i)),
			('<Button-1>', self.focusout),
			('<Return>', self.select),
			('<Escape>', self.close),
			('<MouseWheel>', self.scroll),
			('<Home>', lambda a,i=0: self.move(a,i)),
			('<End>', lambda a,i=END: self.move(a,i)),
			('<Up>', lambda a,i=-1: self.move(a,i)),
			('<Left>', lambda a,i=-1: self.move(a,i)),
			('<Down>', lambda a,i=1: self.move(a,i)),
			('<Right>', lambda a,i=-1: self.move(a,i)),
			('<Prior>', lambda a,i=-10: self.move(a,i)),
			('<Next>', lambda a,i=10: self.move(a,i)),
		]
		for b in bind:
			self.bind(*b)
		scrollbar.config(command=self.listbox.yview)
		if len(list) > 10:
			scrollbar.pack(side=RIGHT, fill=Y)
		self.listbox.pack(side=LEFT, fill=BOTH, expand=1)
		self.focus_set()
		self.update_idletasks()
		size = self.parent.winfo_geometry().split('+',1)[0].split('x')
		if self.parent.winfo_rooty() + self.parent.winfo_reqheight() + self.winfo_reqheight() > self.winfo_screenheight():
			self.geometry('%sx%s+%d+%d' % (size[0],self.winfo_reqheight(),self.parent.winfo_rootx(), self.parent.winfo_rooty() - self.winfo_reqheight()))
		else:
			self.geometry('%sx%s+%d+%d' % (size[0],self.winfo_reqheight(),self.parent.winfo_rootx(), self.parent.winfo_rooty() + self.parent.winfo_reqheight()))
		self.grab_set()
		self.update_idletasks()
		self.wait_window(self)

	def enter(self, e, f):
		self.focus = f

	def focusout(self, e):
		if not self.focus:
			self.select()

	def move(self, e, a):
		if not a in [0,END]:
			a = max(min(self.listbox.size()-1,int(self.listbox.curselection()[0]) + a),0)
		self.listbox.select_clear(0,END)
		self.listbox.select_set(a)
		self.listbox.see(a)

	def scroll(self, e):
		if e.delta > 0:
			self.listbox.yview('scroll', -2, 'units')
		else:
			self.listbox.yview('scroll', 2, 'units')

	def home(self, e):
		self.listbox.yview('moveto', 0.0)

	def end(self, e):
		self.listbox.yview('moveto', 1.0)

	def up(self, e):
		self.listbox.yview('scroll', -1, 'units')

	def down(self, e):
		self.listbox.yview('scroll', 1, 'units')

	def pageup(self, e):
		self.listbox.yview('scroll', -1, 'pages')

	def pagedown(self, e):
		self.listbox.yview('scroll', 1, 'pages')

	def select(self, e=None):
		s = self.listbox.curselection()
		if s:
			self.result = int(s[0])
		self.close()

	def close(self, e=None):
		self.parent.focus_set()
		self.withdraw()
		self.update_idletasks()
		self.destroy()

class CodeText(Frame):
	autoindent = re.compile('^([ \\t]*)')
	selregex = re.compile('\\bsel\\b')

	def __init__(self, parent, ecallback=None, icallback=None, scallback=None, acallback=None, state=NORMAL):
		self.dispatch_output = False
		self.edited = False
		self.taboverride = False
		# Edit Callback
		# INSERT Callback
		# Selection Callback
		# Auto-complete Callback
		self.ecallback = ecallback
		self.icallback = icallback
		self.scallback = scallback
		self.acallback = acallback

		Frame.__init__(self, parent, bd=2, relief=SUNKEN)
		frame = Frame(self)
		font = ('Courier New', -12, 'normal')
		self.lines = Text(frame, height=1, font=font, bd=0, bg='#E4E4E4', fg='#808080', width=8, cursor='')
		self.lines.pack(side=LEFT, fill=Y)
		hscroll = Scrollbar(self, orient=HORIZONTAL)
		self.vscroll = Scrollbar(self)
		self.text = Text(frame, height=1, font=font, bd=0, undo=1, maxundo=100, wrap=NONE, xscrollcommand=hscroll.set, yscrollcommand=self.yscroll, exportselection=0)
		self.text.configure(tabs=self.tk.call("font", "measure", self.text["font"], "-displayof", frame, '    '))
		self.text.pack(side=LEFT, fill=BOTH, expand=1)
		self.text.bind('<Control-a>', lambda e: self.after(1, self.selectall))
		self.text.bind('<Shift-Tab>', lambda e,i=True: self.indent(e, i))
		self.text.bind('<ButtonRelease-3>', self.popup)
		frame.grid(sticky=NSEW)
		hscroll.config(command=self.text.xview)
		hscroll.grid(sticky=EW)
		self.vscroll.config(command=self.yview)
		self.vscroll.grid(sticky=NS, row=0, column=1)
		self.grid_rowconfigure(0,weight=1)
		self.grid_columnconfigure(0,weight=1)

		textmenu = [
			('Undo', self.undo, 0), # 0
			None,
			('Cut', lambda: self.copy(True), 2), # 2
			('Copy', self.copy, 0), # 3
			('Paste', self.paste, 0), # 4
			('Delete', lambda: self.text.delete('Selection.first', 'Selection.last'), 0), # 5
			None,
			('Select All', lambda: self.after(1, self.selectall), 7), # 7
		]
		self.textmenu = Menu(self, tearoff=0)
		for m in textmenu:
			if m:
				l,c,u = m
				self.textmenu.add_command(label=l, command=c, underline=u)
			else:
				self.textmenu.add_separator()

		self.lines.insert('1.0', '      1')
		self.lines.bind('<FocusIn>', self.selectline)
		self.text.mark_set('return', '1.0')
		self.text.orig = self.text._w + '_orig'
		self.tk.call('rename', self.text._w, self.text.orig)
		self.tk.createcommand(self.text._w, self.dispatch)

		self['state'] = state

		self.tag_configure = self.text.tag_configure
		self.tag_add = self.text.tag_add
		self.tag_remove = self.text.tag_remove
		self.tag_raise = self.text.tag_raise
		self.tag_nextrange = self.text.tag_nextrange
		self.tag_prevrange = self.text.tag_prevrange
		self.tag_ranges = self.text.tag_ranges
		self.tag_names = self.text.tag_names
		self.tag_bind = self.text.tag_bind
		self.tag_delete = self.text.tag_delete
		self.mark_set = self.text.mark_set
		self.index = self.text.index
		self.get = self.text.get
		self.see = self.text.see
		self.compare = self.text.compare
		self.edited = False
		self.afterid = None
		self.last_delete = None
		self.tags = {}
		# None - Nothing, True - Continue coloring, False - Stop coloring
		self.coloring = None
		self.dnd = False

		self.setup()

	def popup(self, e):
		if self.text['state'] == NORMAL:
			s,i,r = self.text.index('@1,1'),self.text.index(INSERT),self.text.tag_ranges('Selection')
			try:
				self.text.edit_undo()
			except:
				self.textmenu.entryconfig(0, state=DISABLED)
			else:
				self.text.edit_redo()
				self.textmenu.entryconfig(0, state=NORMAL)
			if r:
				self.tag_add('Selection', *r)
			self.text.mark_set(INSERT,i)
			self.text.yview_pickplace(s)
			s = s.split('.')[0]
			if s in '1 2 3 4 5 6 7 8':
				self.text.yview_scroll(s, 'lines')
			if not self.text.tag_ranges('Selection'):
				sel = DISABLED
			else:
				sel = NORMAL
			for i in [2,3,5]:
				self.textmenu.entryconfig(i, state=sel)
			try:
				c = not self.selection_get(selection='CLIPBOARD')
			except:
				c = 1
			self.textmenu.entryconfig(4, state=[NORMAL,DISABLED][c])
			self.textmenu.post(e.x_root, e.y_root)

	def undo(self):
		self.text.edit_undo()

	def edit_reset(self):
		self.text.edit_reset()

	def copy(self, cut=False):
		self.clipboard_clear()
		self.clipboard_append(self.text.get('Selection.first','Selection.last'))
		if cut:
			r = self.text.tag_ranges('Selection')
			self.text.delete('Selection.first','Selection.last')
			self.update_lines()
			self.update_range('%s linestart' % r[0], '%s lineend' % r[1])

	def paste(self):
		try:
			text = self.selection_get(selection='CLIPBOARD')
		except:
			pass
		else:
			if self.text.tag_ranges('Selection'):
				self.text.mark_set(INSERT, 'Selection.first')
				self.text.delete('Selection.first','Selection.last')
			i = self.text.index(INSERT)
			try:
				self.tk.call(self.text.orig, 'insert', INSERT, text)
			except:
				pass
			self.update_lines()
			self.update_range(i, i + "+%dc" % len(text))

	def focus_set(self):
		self.text.focus_set()

	def __setitem__(self, item, value):
		if item == 'state':
			self.lines['state'] = value
			self.text['state'] = value
		else:
			Frame.__setitem__(self, item, value)

	def selectall(self, e=None):
		self.text.tag_remove('Selection', '1.0', END)
		self.text.tag_add('Selection', '1.0', END)
		self.text.mark_set(INSERT, '1.0')

	def indent(self, e=None, dedent=False):
		item = self.text.tag_ranges('Selection')
		if item and not self.taboverride:
			head,tail = self.index('%s linestart' % item[0]),self.index('%s linestart' % item[1])
			while self.text.compare(head, '!=', END) and self.text.compare(head, '<=', tail):
				if dedent and self.text.get(head) in ' \t':
					self.tk.call(self.text.orig, 'delete', head)
				elif not dedent:
					self.tk.call(self.text.orig, 'insert', head, '\t')
				head = self.index('%s +1line' % head)
			self.update_range(self.index('%s linestart' % item[0]), self.index('%s lineend' % item[1]))
			return True
		elif not item and self.taboverride:
			self.taboverride = False

	def yview(self, *args):
		self.lines.yview(*args)
		self.text.yview(*args)

	def yscroll(self, *args):
		self.vscroll.set(*args)
		self.lines.yview(MOVETO, args[0])

	def selectline(self, e=None):
		self.text.tag_remove('Selection', '1.0', END)
		head = self.lines.index('current linestart')
		tail = self.index('%s lineend+1c' % head)
		self.text.tag_add('Selection', head, tail)
		self.text.mark_set(INSERT, tail)
		self.text.focus_set()

	def setedit(self):
		self.edited = True

	def insert(self, index, text, tags=None):
		if text == '\t':
			if self.last_delete and '\n' in self.last_delete[2]:
				self.tk.call(self.text.orig, 'insert', self.last_delete[0], self.last_delete[2])
				self.tag_add('Selection', self.last_delete[0], self.last_delete[1])
				if self.indent():
					self.setedit()
				return
			if self.acallback != None and self.acallback():
				self.setedit()
				return
		elif self.taboverride and text in self.taboverride and self.last_delete:
			self.tk.call(self.text.orig, 'insert', self.last_delete[0], self.last_delete[2])
			self.taboverride = False
		self.last_delete = None
		self.setedit()
		if text == '\n':
			i = self.index('%s linestart' % index)
			while i != '1.0' and not self.get(i, '%s lineend' % i).split('#',1)[0]:
				i = self.index('%s -1lines' % i)
			m = self.autoindent.match(self.get(i, '%s lineend' % i))
			if m:
				text += m.group(1)
		i = self.text.index(index)
		self.tk.call(self.text.orig, 'insert', i, text, tags)
		self.update_lines()
		self.update_range(i, i + "+%dc" % len(text))

	def delete(self, start, end=None):
		self.after(1, self.setedit)
		try:
			self.tk.call(self.text.orig, 'delete', start, end)
		except:
			pass
		else:
			self.update_lines()
			self.update_range(start)

	def update_lines(self):
		lines = self.lines.get('1.0', END).count('\n')
		dif = self.text.get('1.0', END).count('\n') - lines
		if dif > 0:
			self.lines.insert(END, '\n' + '\n'.join(['%s%s' % (' ' * (7-len(str(n))), n) for n in range(lines+1,lines+1+dif)]))
		elif dif:
			self.lines.delete('%s%slines' % (END,dif),END)

	def update_range(self, start='1.0', end=END):
		self.tag_add("Update", start, end)
		if self.coloring:
			self.coloring = False
		if not self.afterid:
			self.afterid = self.after(1, self.docolor)

	def update_insert(self):
		if self.icallback != None:
			self.icallback()

	def update_selection(self):
		if self.scallback != None:
			self.scallback()

	def dispatch(self, cmd, *args):
		a = []
		if args:
			for n in args:
				if isstr(n):
					a.append(self.selregex.sub('Selection', n))
		a = tuple(a)
		# if self.dispatch_output:
			# sys.stderr.write('%s %s' % (cmd, a))
		if cmd == 'insert':
			self.after(1, self.update_insert)
			self.after(1, self.update_selection)
			return self.insert(*a)
		elif cmd == 'delete':
			self.after(1, self.update_insert)
			self.after(1, self.update_selection)
			# When you press Tab to indent, it actually deletes the selection and then types \t, so we must keep
			#  the last deletion to indent it
			if len(a) == 2 and a[0] == 'Selection.first' and a[1] == 'Selection.last':
				self.last_delete = (self.text.index(a[0]), self.text.index(a[1]), self.text.get(a[0], a[1]))
				def remove_last_delete(*_):
					self.last_delete = None
				self.after(1, remove_last_delete)
			return self.delete(*a)
		elif cmd == 'edit' and a[0] != 'separator':
			self.after(1, self.update_lines)
			self.after(1, self.update_range)
			self.after(1, self.update_insert)
			self.after(1, self.update_selection)
		elif cmd == 'mark' and a[0:2] == ('set', INSERT):
			self.after(1, self.update_insert)
		elif cmd == 'tag' and a[1] == 'Selection' and a[0] in ['add','remove']:
			if self.dnd:
				return ''
			self.after(1, self.update_selection)
		try:
			return self.tk.call((self.text.orig, cmd) + a)
		except TclError:
			return ""

	def setup(self, tags=None):
		r = self.tag_ranges('Selection')
		if self.tags:
			for tag in self.tags.keys():
				self.tag_delete(tag)
		if tags:
			self.tags = tags
		else:
			self.setupparser()
		self.tags['Update'] = {'foreground':None,'background':None,'font':None}
		if not 'Selection' in self.tags:
			self.tags['Selection'] = {'foreground':None,'background':'#C0C0C0','font':None}
		for tag, cnf in self.tags.items():
			if cnf:
				self.tag_configure(tag, **cnf)
		self.tag_raise('Selection')
		if r:
			self.tag_add('Selection', *r)
		self.text.tag_bind('Selection', '<ButtonPress-1>', self.selclick)
		self.text.tag_bind('Selection', '<ButtonRelease-1>', self.selrelease)
		self.text.focus_set()
		self.update_range()

	def docolor(self):
		self.afterid = None
		if self.coloring:
			return
		self.coloring = True
		self.colorize()
		self.coloring = None
		if self.tag_nextrange('Update', '1.0'):
			self.after_id = self.after(1, self.docolor)

	def setupparser(self):
		# Overload to setup your own parser
		pass

	def colorize(self):
		# Overload to do parsing
		pass

	def readlines(self):
		return self.text.get('1.0',END).split('\n')

	def selclick(self, e):
		self.dnd = True
		self.text.bind('<Motion>', self.selmotion)

	def selmotion(self, e):
		self.text.mark_set(INSERT, '@%s,%s' % (e.x,e.y))

	def selrelease(self, e):
		self.dnd = False
		self.text.unbind('<Motion>')
		sel = self.tag_nextrange('Selection', '1.0')
		text = self.text.get(*sel)
		self.delete(*sel)
		self.text.insert(INSERT, text)

class Tooltip:
	def __init__(self, widget, text='', font=None, delay=750, press=False, mouse=False):
		self.widget = widget
		self.setupbinds(press)
		self.text = text
		self.font = font
		self.delay = delay
		self.mouse = mouse
		self.id = None
		self.tip = None
		self.pos = None

	def setupbinds(self, press):
		self.widget.bind('<Enter>', self.enter, '+')
		self.widget.bind('<Leave>', self.leave, '+')
		self.widget.bind('<Motion>', self.motion, '+')
		self.widget.bind('<Button-1>', self.leave, '+')
		if press:
			self.widget.bind('<ButtonPress>', self.leave)

	def enter(self, e=None):
		self.unschedule()
		self.id = self.widget.after(self.delay, self.showtip)

	def leave(self, e=None):
		self.unschedule()
		self.hidetip()

	def motion(self, e=None):
		if self.id:
			self.widget.after_cancel(self.id)
			self.id = self.widget.after(self.delay, self.showtip)

	def unschedule(self):
		if self.id:
			self.widget.after_cancel(self.id)
			self.id = None

	def showtip(self):
		if self.tip:
			return
		self.tip = Toplevel(self.widget, relief=SOLID, borderwidth=1)
		self.tip.wm_overrideredirect(1)
		if is_mac():
			self.tip.wm_transient(self.widget.winfo_toplevel())
		frame = Frame(self.tip, background='#FFFFC8', borderwidth=0)
		Label(frame, text=self.text, justify=LEFT, font=self.font, background='#FFFFC8', relief=FLAT).pack(padx=1, pady=1)
		frame.pack()
		pos = list(self.widget.winfo_pointerxy())
		self.tip.wm_geometry('+%d+%d' % (pos[0],pos[1]+22))
		self.tip.update_idletasks()
		move = False
		if not self.mouse:
			move = True
			pos = [self.widget.winfo_rootx() + self.widget.winfo_reqwidth(), self.widget.winfo_rooty() + self.widget.winfo_reqheight()]
		if pos[0] + self.tip.winfo_reqwidth() > self.tip.winfo_screenwidth():
			move = True
			pos[0] = self.tip.winfo_screenwidth() - self.tip.winfo_reqwidth()
		if pos[1] + self.tip.winfo_reqheight() + 22 > self.tip.winfo_screenheight():
			move = True
			pos[1] -= self.tip.winfo_reqheight() + 44
		if move:
			self.tip.wm_geometry('+%d+%d' % (pos[0],pos[1]+22))

	def hidetip(self):
		if self.tip:
			self.tip.destroy()
			self.tip = None

class TextTooltip(Tooltip):
	def __init__(self, widget, tag, **kwargs):
		self.tag = tag
		kwargs['mouse'] = True
		Tooltip.__init__(self, widget, **kwargs)

	def setupbinds(self, press):
		self.widget.tag_bind(self.tag, '<Enter>', self.enter, '+')
		self.widget.tag_bind(self.tag, '<Leave>', self.leave, '+')
		self.widget.tag_bind(self.tag, '<Motion>', self.motion, '+')
		self.widget.tag_bind(self.tag, '<Button-1>', self.leave, '+')
		if press:
			self.widget.tag_bind(self.tag, '<ButtonPress>', self.leave)

class IntegerVar(StringVar):
	def __init__(self, val='0', range=[None,None], exclude=[], callback=None, allow_hex=False, maxout=None):
		StringVar.__init__(self)
		self.check = True
		self.defaultval = val
		self.lastvalid = val
		self.set(val)
		self.range = range
		self.maxout = maxout
		self.exclude = exclude
		self.callback = callback
		self.allow_hex = allow_hex
		self.is_hex = False
		self.trace('w', self.editvalue)
		self.silence = False

	def editvalue(self, *_):
		#print self.check
		if self.check:
			#print s,self.range
			if self.get(True):
				refresh = True
				try:
					s = self.get()
					if self.range[0] != None and self.range[0] >= 0 and self.get(True).startswith('-'):
						#print '1'
						raise
					if s in self.exclude:
						#print '2'
						raise
					refresh = False
				except:
					#raise
					s = self.lastvalid
				else:
					if self.range[0] != None and s < self.range[0]:
						#print '3'
						s = self.range[0]
						refresh = True
					elif self.range[1] != None and s > self.range[1]:
						#print '4'
						if self.maxout != None:
							s = self.maxout
						else:
							s = self.range[1]
						refresh = True
				#print s
				if refresh:
					if self.is_hex:
						if s == 0:
							self.set('0x')
						else:
							self.set(hex(s))
					else:
						self.set(s)
				if self.callback and not self.silence:
					self.callback(s)
			elif self.range[0] != None:
				s = self.range[0]
			else:
				s = self.defaultval
			self.lastvalid = s
		else:
			self.lastvalid = self.get(True)
			self.check = True

	def set(self, value, silence=False):
		self.silence = silence
		StringVar.set(self, value)
		self.silence = False

	def get(self, s=False):
		string = StringVar.get(self)
		if s:
			return string
		if self.allow_hex and string.startswith('0x'):
			self.is_hex = True
			if string == '0x':
				return 0
			return int(string, 16)
		self.is_hex = False
		return int(string or 0)

	def setrange(self, range):
		self.range = list(range)
		value = self.get()
		new_value = max(range[0],min(range[1],value))
		if new_value != value:
			self.set(new_value)

class FloatVar(IntegerVar):
	def __init__(self, val='0', range=[None,None], exclude=[], callback=None, precision=None):
		self.precision = precision
		IntegerVar.__init__(self, val, range, exclude, callback)

	def editvalue(self, *_):
		if self.check:
			s = self.get(True)
			if s:
				try:
					if self.range[0] != None and self.range[0] >= 0 and self.get(True).startswith('-'):
						raise
					isfloat = self.get(True)
					s = self.get()
					if s in self.exclude:
						raise
					s = str(s)
					if self.precision and not s.endswith('.0') and len(s)-s.index('.')-1 > self.precision:
						raise
					if not isfloat.endswith('.') and not isfloat.endswith('.0') and s.endswith('.0'):
						s = s[:-2]
						s = int(s)
					else:
						s = float(s)
				except:
					s = self.lastvalid
				else:
					if self.range[0] != None and s < self.range[0]:
						s = self.range[0]
					elif self.range[1] != None and s > self.range[1]:
						s = self.range[1]
				self.set(s)
				if self.callback:
					self.callback(s)
			elif self.range[0] != None:
				s = self.range[0]
			else:
				s = self.defaultval
			self.lastvalid = s
		else:
			self.lastvalid = self.get(True)
			self.check = True

	def get(self, s=False):
		if s:
			return StringVar.get(self)
		return float(StringVar.get(self))

class SStringVar(StringVar):
	def __init__(self, val='', length=0, callback=None):
		StringVar.__init__(self)
		self.check = True
		self.length = length
		self.lastvalid = val
		self.set(val)
		self.callback = callback
		self.trace('w', self.editvalue)

	def editvalue(self, *_):
		if self.check:
			s = self.get()
			if self.length and len(s) > self.length:
				self.set(self.lastvalid)
			else:
				self.lastvalid = s
				if self.callback:
					self.callback(s)
		else:
			self.lastvalid = self.get()
			self.check = True

class odict:
	def __init__(self, d=None, k=None):
		self.keynames = []
		self.dict = {}
		if d:
			if k:
				self.keynames = list(k)
				self.dict = dict(d)
			else:
				self.keynames = list(d.keynames)
				self.dict = dict(d.dict)

	def __delitem__(self, key):
		del self.dict[key]
		self.keynames.remove(key)

	def __setitem__(self, key, item):
		self.dict[key] = item
		if key not in self.keynames:
			self.keynames.append(key)

	def __getitem__(self, key):
		return self.dict[key]

	def __contains__(self, key):
		if key in self.keynames:
			return True
		return False

	def __len__(self):
		return len(self.keynames)

	def iteritems(self):
		iter = []
		for k in self.keynames:
			iter.append((k,self.dict[k]))
		return iter

	def iterkeys(self):
		return list(self.keynames)

	def peek(self):
		return (self.keynames[0],self.dict[self.keynames[0]])

	def keys(self):
		return list(self.keynames)

	def index(self, key):
		return self.keynames.index(key)

	def get(self, key, default=None):
		if not key in self.keynames:
			return default
		return self.dict[key]

	def getkey(self, n):
		return self.keynames[n]

	def getitem(self, n):
		return self.dict[self.keynames[n]]

	def remove(self, n):
		self.keynames.remove(n)
		del self.dict[n]

	def __repr__(self):
		return '%s@%s' % (self.keynames,self.dict)

	def copy(self):
		return odict(self)

	def sort(self):
		self.keynames.sort()

def get_umask():
	umask = os.umask(0)
	os.umask(umask)
	return umask

def create_temp_file(name, createmode=None):
	directory, filename = os.path.split(name)
	handle, temp_file = tempfile.mkstemp(prefix=".%s-" % filename, dir=directory)
	os.close(handle)

	try:
		mode = os.lstat(name).st_mode & 0o777
	except OSError as e:
		if e.errno != errno.ENOENT:
			raise
		mode = createmode
		if mode == None:
			mode = ~get_umask()
		mode &= 0o666
	os.chmod(temp_file, mode)

	return temp_file

class AtomicWriter:
	def __init__(self, path, mode="w+b", createmode=None, encoding=None):
		self.real_file = path
		self.handle = None
		self.temp_file = None

		if os.path.isfile(path):
			temp_file = create_temp_file(path, createmode=createmode)
			if encoding:
				self.handle = codecs.open(temp_file, mode, encoding)
			else:
				self.handle = open(temp_file, mode)
			self.temp_file = temp_file
		else:
			self.handle = open(path, mode)

		self.write = self.handle.write
		self.fileno = self.handle.fileno

	def close(self):
		if self.handle and not self.handle.closed:
			self.handle.flush()
			os.fsync(self.handle.fileno())
			self.handle.close()
		if self.temp_file:
			bak_file = None
			if os.path.isfile(self.real_file):
				directory, filename = os.path.split(self.real_file)
				bak_name = '.%s~' % filename
				while os.path.isfile(os.path.join(directory,bak_name)):
					bak_name += '~'
				bak_file = os.path.join(directory, bak_name)
				try:
					os.rename(self.real_file, bak_file)
				except:
					bak_file = None
					pass
			try:
				os.rename(self.temp_file, self.real_file)
			except Exception, e:
				if bak_file:
					try:
						os.rename(bak_file, self.real_file)
					except:
						pass
				raise PyMSError('Save', "File already exists and cannot be modified")
			finally:
				if bak_file:
					try:
						os.remove(bak_file)
					except:
						pass

	def discard(self):
		if self.handle and not self.handle.closed:
			self.handle.close()
		if self.temp_file:
			try:
				os.remove(self.temp_file)
			except:
				pass

	def __del__(self):
		self.discard()

def apply_cursor(widget, cursors):
	for cursor in reversed(cursors):
		try:
			widget.config(cursor=cursor)
			return cursor
		except:
			pass

class Action:
	def __init__(self):
		pass

	def has_changes(self):
		return False

	def update_display(self, info=None):
		pass

	def undo(self):
		pass

	def redo(self):
		pass

class ActionUpdateValues(Action):
	def __init__(self, obj, attrs):
		Action.__init__(self)
		self.start_values = {}
		for attr in attrs:
			if hasattr(obj, attr):
				self.start_values[attr] = copy.deepcopy(getattr(obj, attr))
		self.end_values = None

	def set_end_values(self, obj, attrs):
		self.end_values = {}
		for attr in attrs:
			if hasattr(obj, attr):
				self.end_values[attr] = copy.deepcopy(getattr(obj, attr))

	def has_changes(self):
		return (self.start_values != self.end_values)

	def get_obj(self):
		return None

	def apply_values(self, obj, from_values, to_values):
		from_attrs = set(from_values.keys())
		to_attrs = set(to_values.keys())
		del_attrs = from_attrs - to_attrs
		for attr in del_attrs:
			delattr(obj, attr)
		for name in to_attrs:
			setattr(obj, name, copy.deepcopy(to_values[name]))

	def undo(self):
		self.apply_values(self.get_obj(), self.end_values, self.start_values)
		self.update_display(self.start_values)

	def redo(self):
		self.apply_values(self.get_obj(), self.start_values, self.end_values)
		self.update_display(self.end_values)

class ActionUpdateArray(Action):
	def __init__(self):
		self.start_values = []
		self.end_values = []

	def update_values(self, obj, indices, values):
		for indexes,v in zip(indices,values):
			array = obj
			i = 0
			while len(indexes) - i:
				array = array[indexes[i]]
				i += 1
			self.start_values.append((indexes, array[indexes[i]]))
			self.end_values.append((indexes, v))

	def update_value(self, obj, indices, value):
		self.update_values(obj, indices, (value,) * len(indices))

	def has_changes(self):
		return (self.start_values != self.end_values)

	def apply_values(self, obj, values):
		for indexes,v in values:
			array = arrays
			i = 0
			while len(indexes) - i:
				array = array[indexes[i]]
				i += 1
			array[indexes[i]] = v

	def get_obj(self):
		return None

	def undo(self):
		self.apply_values(self.get_obj(), self.start_values)
		self.update_display(self.start_values)

	def redo(self):
		self.apply_values(self.get_obj(), self.end_values)
		self.update_display(self.end_values)

class ActionGroup(Action):
	def __init__(self):
		self.actions = []
		self.complete = False

	def add_action(self, action):
		group = None
		if self.actions:
			group = self.actions[-1]
		if isinstance(group, ActionGroup) and not group.complete:
			group.add_action(action)
		else:
			self.actions.append(action)

	def remove_action(self, action):
		self.actions.remove(action)

	def has_changes(self):
		for action in self.actions:
			if action.has_changes():
				return True
		return False

	def undo(self):
		for action in reversed(self.actions):
			action.undo()

	def redo(self):
		for action in self.actions:
			action.redo()

class ActionManager(ActionGroup):
	def __init__(self):
		ActionGroup.__init__(self)
		self.redos = []

	def get_open_group(self):
		parent,group = self,self
		while isinstance(group, ActionGroup) and group.actions and isinstance(group.actions[-1], ActionGroup) and not group.actions[-1].complete:
			parent = group
			group = group.actions[-1]
		return (parent,group)

	def start_group(self):
		self.add_action(ActionGroup())

	def end_group(self):
		parent,open_group = self.get_open_group()
		if open_group != self:
			open_group.complete = True
			if not open_group.has_changes():
				parent.remove_action(open_group)
			elif len(open_group.actions) == 1:
				parent.add_action(open_group.actions[0])
				parent.remove_action(open_group)

	def add_action(self, action):
		self.redos = []
		ActionGroup.add_action(self, action)

	def can_undo(self):
		return (len(self.actions) > 0)

	def undo(self):
		if self.can_undo():
			action = self.actions[-1]
			self.redos.append(action)
			del self.actions[-1]
			action.undo()

	def can_redo(self):
		return (len(self.redos) > 0)

	def redo(self):
		if self.can_redo():
			action = self.redos[-1]
			self.actions.append(action)
			del self.redos[-1]
			action.redo()

class FFile:
	def __init__(self):
		self.data = ''

	def read(self):
		return self.data

	def write(self, data):
		self.data += data

	def close(self):
		pass
