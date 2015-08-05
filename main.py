# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function

import re
import pexpect

from prompt_toolkit.shortcuts import get_input
from prompt_toolkit.history import History
from prompt_toolkit.contrib.completers import WordCompleter
from pygments.lexers import IokeLexer

IOKE = '/usr/bin/env ioke'
IOKE_VOCAB  = ['method'] # TODO
IOKE_PROMPT = 'iik> '
IOKE_DEBUG = 'dbg:1> ' # TODO: regexp
IOKE_EVAL = '+> '

# TODO: colors
IN_PROMPT = "In [{}]: "
OUT_PROMPT = "Out [{}]:"
DBG_PROMPT = "Choose a restart: "

RESULT_RE = re.compile(r'^\+\>(.*)', re.MULTILINE)

ioke_completer = WordCompleter(IOKE_VOCAB)

class ExitRepl(Exception):
    pass

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

    def execute(self, expression):
        self.last_input = expression
        self._process.sendline(expression)

# TODO:
# - Repl class
# - Multiline mode
# - Menus


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
                text = get_input(IN_PROMPT.format(line_num), lexer=IokeLexer,
                    history=self._history, completer=ioke_completer)
            else:
                text = get_input(DBG_PROMPT)
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
            # TODO: deal with conditions (debug prompt)
            if text:
                self.prompt = prompt = self.execute(text)
                if prompt == IOKE_PROMPT:
                    self.condition = False
                    printed, result = self._ioke.output
                    if printed:
                        print(printed)
                    if result != 'nil':
                        print(OUT_PROMPT.format(line_num), result)
                elif prompt == IOKE_DEBUG:
                    self.condition = True
                    options, _ = self._ioke.output
                    print(options.strip())
                    # TODO:
                    # - Format and colorise traceback/options
                    # - Validate and send choice
                    # - loop until condition is resolved
                print()
                self.inc_line()

if __name__ == '__main__':
    repl = Repl()
    repl.main_loop()
