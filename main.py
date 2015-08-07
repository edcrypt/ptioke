# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function

import re
import pexpect

from prompt_toolkit.shortcuts import get_input
from prompt_toolkit.history import History
from prompt_toolkit.contrib.completers import WordCompleter
from pygments.lexers import IokeLexer
from pygments.style import Style
from pygments.token import Token
from pygments.styles.default import DefaultStyle


IOKE = '/usr/bin/env ioke'
IOKE_VOCAB  = ['method'] # TODO
IOKE_PROMPT = 'iik> '
IOKE_DEBUG = r'dbg:([0-9]+?)([:]\w+?)?> '
IOKE_EVAL = '+> '

# TODO: colors
OUT_PROMPT = "Out [{}]: {}"

ioke_completer = WordCompleter(IOKE_VOCAB)

class ExitRepl(Exception):
    pass

class DocumentStyle(Style):
    styles = {
        # completition menu
        Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
        Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
        Token.Menu.Completions.ProgressButton: 'bg:#003333',
        Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',

        # prompt
        Token.Prefix: '#884444',
        Token.OpenBracket: '#00aa00',
        Token.CloseBracket: '#00aa00',
        Token.LineNum: '#BB0000',
        Token.Collon: '#884444',

        # condition
        Token.ConditionPrefix: '#BB0000',
        Token.Sharp: '#884444',
        Token.ConditionNumber: '#BB0000',
        Token.Separator: '#FFFFFF',
        Token.ChooseRestart: '#FFFFFF underline',

        # restart
        Token.Restart: '#0000FF',
        Token.ArgsArrow: '#FFFFFF',
    }
    styles.update(DefaultStyle.styles)


class IokeShell(object):
    """ Provides comunication with external Ioke process.
    """
    command_prompt = IOKE_PROMPT
    debug_prompt = IOKE_DEBUG
    prompts = [IOKE_PROMPT, IOKE_DEBUG]
    last_input = ""

    def __init__(self, ioke_command=IOKE, spawner=pexpect.spawnu):
        self._process = None
        self._spawner = spawner
        self._ioke_command = ioke_command

    def start(self):
        self._process = self._spawner(self._ioke_command)
        self._process.setecho(False)

    @property
    def current_prompt(self):
        prompt = self._process.expect(self.prompts)
        return self.prompts[prompt]

    @property
    def output(self):
        evalued = ''
        stdout = self._process.before
        if IOKE_EVAL in stdout:
            stdout, _, evalued = stdout.partition(IOKE_EVAL)
            evalued = evalued.strip()
        stdout = stdout.replace(self.last_input, "").strip()
        return stdout, evalued

    @property
    def debug_level(self):
        return self._process.match.groups()[0]

    @property
    def restart(self):
        return self._process.match.groups()[1]

    def execute(self, expression):
        self.last_input = expression
        self._process.sendline(expression)

# TODO:
# - Out [n]: prompt after restart with multiple returns
# - Repl banner
# - Vi/Emacs mode
# - System commands - https://github.com/jonathanslenders/python-prompt-toolkit/blob/master/examples/system-prompt.py
# - Multiline mode - https://github.com/jonathanslenders/python-prompt-toolkit/blob/master/examples/get-multiline-input.py
# - Keybinding for multiline mode - https://github.com/jonathanslenders/python-prompt-toolkit/blob/master/examples/get-password-with-toggle-display-shortcut.py
# - Persistent history - https://github.com/jonathanslenders/python-prompt-toolkit/blob/master/examples/persistent-history.py
# - Toolbar - https://github.com/jonathanslenders/python-prompt-toolkit/blob/master/examples/bottom-toolbar.py

class Repl(object):
    """ Main REPL implementation.
    """
    def __init__(self):
        self._ioke = IokeShell()
        self._history = History()
        self.prompt = None
        self._input_text = None
        self.line_num = 1
        self.condition = False
        self.debug_level = 1
        self.restart = None

    def _run_subprocess(self):
        self._ioke.start()

    def main_loop(self):
        self._run_subprocess()
        while True:
            try:
                self.process_io()
            except ExitRepl:
                break
        print("Goodbye")

    def get_in_prompt_tokens(self, cli):
        return [
            (Token.Prefix, 'In '),
            (Token.OpenBracket, '['),
            (Token.LineNum, str(self.line_num)),
            (Token.CloseBracket, ']'),
            (Token.Collon, ': '),
        ]

    def get_condition_prompt_tokens(self, cli):
        return [
            (Token.ConditionPrefix, 'ERR! '),
            (Token.Sharp, '#'),
            (Token.ConditionNumber, str(self.debug_level)),
            (Token.Separator, ' - '),
            (Token.ChooseRestart, 'Choose a restart'),
            (Token.Collon, ': ')
        ]

    def get_restart_prompt_tokens(self, cli):
        return [
            (Token.Restart, '    {}'.format(self.restart)),
            (Token.ArgArrow, ' => '),
        ]

    def execute(self, text):
        self._ioke.execute(text)
        try:
            return self._ioke.current_prompt
        except pexpect.EOF as err:
            raise ExitRepl(err)

    def inc_line(self, n=1):
        self.line_num += n

    def process_io(self):
        text = self._input_text
        line_num = self.line_num
        try:
            if not self.condition:
                text = get_input(
                    get_prompt_tokens=self.get_in_prompt_tokens, lexer=IokeLexer,
                    history=self._history, completer=ioke_completer, style=DocumentStyle)
            else:
                if self.restart is not None:
                    text = get_input(
                        get_prompt_tokens=self.get_restart_prompt_tokens,
                        style=DocumentStyle)
                else:
                    text = get_input(
                        get_prompt_tokens=self.get_condition_prompt_tokens,
                        style=DocumentStyle)
            self._input_text = text
            if self.prompt is None:
                self.prompt = self._ioke.current_prompt
        except (EOFError, pexpect.EOF) as err:
            raise ExitRepl(err)
        except KeyboardInterrupt:
            self._input_text = text = ""
            print("**Keyboard interrupt**")
            print("Enter ctrl-d to exit")
        else:
            if text:
                self.prompt = prompt = self.execute(text)
                if prompt == IOKE_PROMPT:
                    self.condition = False
                    printed, result = self._ioke.output
                    if printed:
                        print(printed)
                    if result != 'nil':
                        print(OUT_PROMPT.format(line_num, result))
                    print()
                elif prompt == IOKE_DEBUG:
                    self.condition = True
                    options, _ = self._ioke.output
                    self.debug_level = self._ioke.debug_level
                    self.restart = self._ioke.restart
                    options = options.strip()
                    if options:
                        print(options)
                    # TODO: Format and colorise traceback/options
                self.inc_line()

if __name__ == '__main__':
    repl = Repl()
    repl.main_loop()
