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
#IOKE_RESULT = '\+> .*'

IN_PROMPT = "In [{}]: "
OUT_PROMPT = "Out [{}]:"

RESULT_RE = re.compile(r'^\+\>(.*)', re.MULTILINE)

ioke_completer = WordCompleter(IOKE_VOCAB)

class IokeShell(object):
    command_prompt = IOKE_PROMPT
    debug_prompt = IOKE_DEBUG
    prompts = [IOKE_PROMPT, IOKE_DEBUG]

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
        # TODO: Parse prints and +> (result)
        result = RESULT_RE.findall(self._process.before)
        if result is None:
            return
        else:
            return result[0].strip()

    def execute(self, expression):
        self._process.sendline(expression)

def main():
    ioke = IokeShell()
    ioke.start()
    history = History()
    text = None
    line_num = 1
    prompt = None
    while True:
        try:
            text = get_input(IN_PROMPT.format(line_num), lexer=IokeLexer,
                history=history, completer=ioke_completer)
            if prompt is None:
                prompt = ioke.current_prompt
        except EOFError:
            break
        except KeyboardInterrupt:
            text = ""
        else:
            # TODO: deal with conditions (debug prompt)
            if text:
                ioke.execute(text)
                prompt = ioke.current_prompt
                if prompt == IOKE_PROMPT:
                    print(OUT_PROMPT.format(line_num), ioke.output)
                print()
                line_num += 1
    print("Goodbye")

if __name__ == '__main__':
    main()
