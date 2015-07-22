import os
import sublime, sublime_plugin
from Emacs.libemacs import Emacs

emacs = Emacs()

class EmacsEvalCommand(sublime_plugin.TextCommand):
    def run(self, edit, body):
        view = self.view
        file_name = self.view.file_name()
        _, file_ext = os.path.splitext(file_name)
        sel = view.sel()
        beg = sel[0].begin()
        end = sel[0].end()
        buffer_region = sublime.Region(0, view.size())
        buffer_string = view.substr(buffer_region)
        new_buffer_string, stdout = emacs.eval_in_buffer_string(buffer_string,
                                                                body,
                                                                beg, end, file_ext=file_ext)
        print('stdout', stdout)
        view.replace(edit, buffer_region, new_buffer_string)
        def to_int(x):
            try: return int(float(x))
            except: return 0
        mark, point, mark_active = map(to_int, stdout[1:-2].split())
        if not mark_active or not point:
            mark = point
        sel.clear()
        sel.add(sublime.Region(mark, point))

class EmacsKillDaemonCommand(sublime_plugin.WindowCommand):
    def run(self):
        emacs.eval("(kill-emacs)")

class EmacsOpenCurrentFileCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        file_name = self.view.file_name()
        (row,col) = self.view.rowcol(self.view.sel()[0].begin())
        emacs.open_file(file_name, row+1, col+1)