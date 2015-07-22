import os
import sublime, sublime_plugin
from Emacs.libemacs import Emacs

emacs = Emacs()

class EmacsKillDaemonCommand(sublime_plugin.WindowCommand):
    def run(self):
        emacs.kill()

class EmacsOpenCurrentFileCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        file_name = self.view.file_name()
        (row,col) = self.view.rowcol(self.view.sel()[0].begin())
        emacs.open_file(file_name, row+1, col+1)

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
        new_buffer_string = emacs.eval_in_buffer_string(buffer_string,
                                                          interactive_command, beg, end, file_ext=file_ext)

        view.replace(edit, buffer_region, new_buffer_string)
