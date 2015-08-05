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
IOKE_DEBUG = 'dbg:1> '
IOKE_EVAL = '+> '

# TODO: colors
IN_PROMPT = "In [{}]: "
OUT_PROMPT = "Out [{}]:"
DBG_PROMPT = "Err! [{}]: "

RESULT_RE = re.compile(r'^\+\>(.*)', re.MULTILINE)

ioke_completer = WordCompleter(IOKE_VOCAB)

class IokeShell(object):
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
        stdout, evalued = '', ''
        output = self._process.before
        if IOKE_EVAL in output:
            stdout, _, evalued = output.partition(IOKE_EVAL)
            stdout = stdout.replace(self.last_input, "").strip()
            evalued = evalued.strip()
        return stdout, evalued

    def execute(self, expression):
        self.last_input = expression
        self._process.sendline(expression)

# TODO: Repl class
def main():
    ioke = IokeShell()
    ioke.start()
    history = History()
    text = None
    line_num = 1
    prompt = None
    condition = False
    while True:
        try:
            if not condition:
                text = get_input(IN_PROMPT.format(line_num), lexer=IokeLexer,
                history=history, completer=ioke_completer)
            else:
                choice = get_input(DBG_PROMPT.format(1))
            if prompt is None:
                prompt = ioke.current_prompt
        except EOFError:
            break
        except KeyboardInterrupt:
            text = ""
        else:
            # TODO: deal with conditions (debug prompt)
            if text and not condition:
                ioke.execute(text)
                prompt = ioke.current_prompt
                if prompt == IOKE_PROMPT:
                    printed, result = ioke.output
                    print(printed)
                    if result != 'nil':
                        print(OUT_PROMPT.format(line_num), result)
                elif prompt == IOKE_DEBUG:
                    condition = True
                    # TODO:
                    # - Parse and show options
                    # - Validate and send choice
                    # - loop until condition is resolved
                print()
                line_num += 1
    print("Goodbye")

if __name__ == '__main__':
    main()
