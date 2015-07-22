import sublime, sublime_plugin
import os, sys, subprocess
import tempfile
import re

# Daemon Emacs working as a service
EMACSCLIENT = '/usr/local/bin/emacsclient'
EMACS = '/usr/local/Cellar/emacs/24.5/Emacs.app/Contents/MacOS/Emacs'
EMACS_PARAM = ['--geometry', '166x46']

SOCKET = '/tmp/sublime/server'
INIT_FILE = '~/Downloads/sublime.el'

# Aternate editor, useful for OS X: Mac-Port version crashes silently
# when open org file in terminal but works just fine for the Gui
# version.
ALTERNATE_EDITOR = ['open', '-a', '/opt/homebrew-cask/Caskroom/emacs-mac/emacs-24.5-z-mac-5.8/Emacs.app', '--args']

def flatten_cmd(*cmd):
	flat_cmd = []
	for c in cmd:
		if not isinstance(c, str):
			flat_cmd.extend(flatten_cmd(*c))
		else:
			flat_cmd.append(c)
	return flat_cmd

def subprocess_exit_code_and_output(*cmd):
	flat_cmd = flatten_cmd(*cmd)
	pipe = subprocess.Popen(flat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = pipe.communicate()
	return pipe.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')

def emacsclient(*args, wait=True):
	# FIXME: Expensive version
	# TODO: Using socket directly should be much faster, no process, no command line...
	check_cmd = [EMACSCLIENT, '-s', SOCKET, '-e', 'nil']
	exit_code, _, _ = subprocess_exit_code_and_output(check_cmd)
	if exit_code != 0:
		subprocess_exit_code_and_output(EMACS, '-q', '-l', INIT_FILE, '--daemon')
		if not os.path.exists(SOCKET):
			raise Exception('Failed to start Emacs Daemon')
	open_cmd = [EMACSCLIENT, '-s', SOCKET]
	open_cmd.extend(list(args))
	if wait:
		return subprocess_exit_code_and_output(open_cmd)
	else:
		subprocess.Popen(flatten_cmd(open_cmd))
		return 0, '', ''

def kill_daemon():
	src = """(kill-emacs)"""
	cmd = ['-e', src]
	exit_code, _, _ = emacsclient(cmd)

def eval_in_file(file_name, commands, mark=0, point=0):
	if point == mark: mark_active = 'nil'
	else: mark_active = 't'

	src = """
		(progn
		  (find-file "%s")
		  (set-mark %d)
		  (goto-char %d)
		  (setq mark-active %s)
		  %s
		  (save-buffer)
		  (kill-buffer)
		  (list (mark) (point) mark-active))
		""" % (file_name, mark, point, mark_active, commands)
	cmd = ['-e', src]
	exit_code, _, _ = emacsclient(cmd)
	return exit_code

def eval_in_buffer_string(buffer_string, commands, mark=0, point=0, file_ext='.txt'):
	f = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, mode='wb')
	temp_file_name = f.name
	f.write(buffer_string.encode('utf-8'))
	f.close()
	eval_in_file(temp_file_name, commands, mark, point)
	with open(temp_file_name, 'rb') as f:
		return f.read().decode('utf-8')
	# TODO: Remove temporary file

def open_in_emacs(file_name, row, col):
	check_cmd = [EMACSCLIENT, '-e', '"t"']
	exit_code, _, _ = subprocess_exit_code_and_output(check_cmd)
	if exit_code == 0:
		open_cmd = [EMACSCLIENT, '-n', '+%d:%d'%(row, col), file_name]
	else:
		if ALTERNATE_EDITOR:
			open_cmd = [ALTERNATE_EDITOR, EMACS_PARAM, '+%d:%d'%(row, col), file_name]
		else:
			open_cmd = [EMACS, EMACS_PARAM, '+%d:%d'%(row, col), file_name]

	subprocess.Popen(flatten_cmd(open_cmd))

class EmacsKillDaemonCommand(sublime_plugin.WindowCommand):
	def run(self):
		kill_daemon()

class EmacsOpenCurrentFileCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		file_name = self.view.file_name()
		(row,col) = self.view.rowcol(self.view.sel()[0].begin())
		open_in_emacs(file_name, row+1, col+1)

class EmacsCallInteractivelyCommand(sublime_plugin.TextCommand):
	def run(self, edit, command):
		view = self.view
		file_name = self.view.file_name()
		_, file_ext = os.path.splitext(file_name)
		beg = view.sel()[0].begin()
		end = view.sel()[0].end()
		buffer_region = sublime.Region(0, view.size())
		buffer_string = view.substr(buffer_region)

		interactive_command = "(call-interactively '%s)" % command
		new_buffer_string = eval_in_buffer_string(buffer_string,
								interactive_command, beg, end, file_ext=file_ext)

		view.replace(edit, buffer_region, new_buffer_string)
