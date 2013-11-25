# Helper functions and classes to wrap common Sublime Text idioms:
#
import functools
import os

import sublime
import sublime_plugin


def main_thread(callback, *args, **kwargs):

    sublime.set_timeout_async(functools.partial(callback, *args, **kwargs), 0)


class TextCommand(sublime_plugin.TextCommand):

    def get_region(self, view=None):
        '''Get the value under the cursor, or cursors.'''

        value = ''

        if view is None:
            view = self.view

        # If there is no view then all bets are off:
        #
        if view is not None:

            # Get the selection:
            #
            selection = view.sel()
            if selection is not None:

                # For each region in the selection, either use it directly,
                # or expand it to take in the 'word' that the cursor is on:
                #
                for region in selection:
                    if region.empty():
                        region = view.expand_by_class(
                            region,
                            sublime.CLASS_WORD_START | sublime.CLASS_WORD_END,
                            ' ():'
                        )
                    value = value + ' ' + view.substr(region)

        return value

    def get_working_dir(self):
        '''Get the view's current working directory.'''

        view = self.view

        if view is not None:

            # If there is a file in the active view then use it to work out
            # a working directory:
            #
            file_name = view.file_name()
            if file_name is not None:
                dirname, _ = os.path.split(os.path.abspath(file_name))
                return dirname

            window = view.window()
            if window is not None:

                # If there is a project file in the window then use it to work
                # out a working directory:
                #
                file_name = window.project_file_name()
                if file_name is not None:
                    dirname, _ = os.path.split(os.path.abspath(file_name))
                    return dirname

                # Alternatively, see if there are any open folders, and if so, use the
                # path of the first one:
                #
                folders = window.folders()
                if folders is not None:
                    return folders[0]

        return ''


# The command that is executed to insert text into a view:
#
class SublimeHelperInsertTextCommand(sublime_plugin.TextCommand):

    def run(self, edit, pos, msg):

        if msg is not None:
            self.view.insert(edit, pos, msg)


# The command that is executed to erase text in a view:
#
class SublimeHelperEraseTextCommand(sublime_plugin.TextCommand):

    def run(self, edit, a, b):

        self.view.erase(edit, sublime.Region(a, b))


# The command that is executed to clear a buffer:
#
class SublimeHelperClearBufferCommand(sublime_plugin.TextCommand):

    def run(self, edit):

        view = self.view
        view.run_command('sublime_helper_erase_text', {'a': 0, 'b': view.size()})


class OutputTarget():

    def __init__(self, window, data_key, command, working_dir, title=None, syntax=None, panel=False, console=None):

        # If a panel has been requested then create one and show it,
        # otherwise create a new buffer, and set its caption:
        #
        if console is not None:
            self.console = console
        else:
            if panel is True:
                self.console = window.get_output_panel('ShellCommand')
                window.run_command('show_panel', {'panel': 'output.ShellCommand'})
            else:
                self.console = window.new_file()
                caption = title if title else '*Shell Command Output*'
                self.console.set_name(caption)

            # Indicate that this buffer is a scratch buffer:
            #
            self.console.set_scratch(True)
            self.console.set_read_only(True)

            # Set the syntax for the output:
            #
            if syntax is not None:
                resources = sublime.find_resources(syntax + '.tmLanguage')
                self.console.set_syntax_file(resources[0])

            # Set a flag on the view that we can use in key bindings:
            #
            settings = self.console.settings()
            settings.set(data_key, True)

            # Also, save the command and working directory for later,
            # since we may need to refresh the panel/window:
            #
            data = {
                'command': command,
                'working_dir': working_dir
            }
            settings.set(data_key + '_data', data)

    def append_text(self, output):

        console = self.console

        # Insert the output into the buffer:
        #
        console.set_read_only(False)
        console.run_command('sublime_helper_insert_text', {'pos': console.size(), 'msg': output})
        console.set_read_only(True)

    def set_status(self, tag, message):

        self.console.set_status(tag, message)
