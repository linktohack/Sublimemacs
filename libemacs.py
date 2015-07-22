import os, subprocess
import tempfile

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

def _flatten(*cmd):
    flat_cmd = []
    for c in cmd:
        if not isinstance(c, str):
            flat_cmd.extend(_flatten(*c))
        else:
            flat_cmd.append(c)
    return flat_cmd

def _exec(*cmd, wait=True):
    flat_cmd = _flatten(*cmd)
    pipe = subprocess.Popen(flat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if wait:
        stdout, stderr = pipe.communicate()
        return pipe.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')
    else:
        return None, '', ''

class Emacs:
    def __init__(self, client=EMACSCLIENT, emacs=EMACS, param=EMACS_PARAM,
                 alternate_editor=ALTERNATE_EDITOR,
                 socket=SOCKET, init_file=INIT_FILE):
        self.client = client
        self.emacs = emacs
        self.param = param
        self.alternate_editor = alternate_editor
        self.socket = socket
        self.init_file = init_file
        
    def _maybe_start_emacs(self):
        # TODO: Expensive version
        #       Using socket directly should be much faster, no process, no command line...
        check_cmd = [self.client, '-s', self.socket, '-e', 'nil']
        exit_code, _, _ = _exec(check_cmd)
        if exit_code != 0:
            _exec(self.emacs, '-q', '-l', self.init_file, '--daemon')
            if not os.path.exists(self.socket):
                raise Exception('Failed to start Emacs Daemon')

    def eval(self, *body):
        self._maybe_start_emacs()
        return _exec([self.client, '-s', self.socket, '-e', body], wait=True)

    def eval_in_file(self, file_name, commands, mark=0, point=0):
        if point == mark: mark_active = 'nil'
        else: mark_active = 't'
        body = """
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
        return self.eval(body)

    def eval_in_buffer_string(self, buffer_string, commands, mark=0, point=0, file_ext='.txt'):
        temp_file = tempfile.mkstemp(suffix=file_ext)[1]
        with open(temp_file, 'wb') as f:
            f.write(buffer_string.encode('utf-8'))
        exit_code, stdout, stderr = self.eval_in_file(temp_file, commands, mark, point)
        if exit_code != 0:
            raise Exception('Failed to evaluate body')
        with open(temp_file, 'rb') as f:
            new_buffer_string = f.read().decode('utf-8')
        os.unlink(temp_file)
        return new_buffer_string, stdout

    def open_file(self, file_name, row, col):
        check_cmd = [self.client, '-e', 't']
        exit_code, _, _ = _exec(check_cmd)
        if exit_code == 0:
            open_cmd = [self.client, '-n', '+%d:%d'%(row, col), file_name]
        else:
            if self.alternate_editor:
                open_cmd = [self.alternate_editor, self.param, '+%d:%d'%(row, col), file_name]
            else:
                open_cmd = [self.emacs, self.param, '+%d:%d'%(row, col), file_name]
        _exec(open_cmd, wait=False)

    def kill(self):
        exit_code, _, _ = self.eval('(kill-emacs)')
