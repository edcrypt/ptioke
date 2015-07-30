# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function

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

ioke_completer = WordCompleter(IOKE_VOCAB)

class IokeShell(object):
    command_prompt = IOKE_PROMPT
    debug_prompt = IOKE_DEBUG
    prompts = (IOKE_PROMPT, IOKE_DEBUG)

    def __init__(self, ioke_command=IOKE, spawner=pexpect.spawnu):
        self._process = None
        self._spawner = spawner
        self._ioke_command = ioke_command

    def start(self):
        assert self._process is not None
        self._process = self._spawner(self.ioke_command)

    @property
    def current_prompt(self):
        return self.prompts[self._process.expect(self.prompts)]

    @property
    def output(self):
        # TODO: Parse prints and +> (result)
        return self._process.before

    def execute(self, expression):
        self._process.sendline(expression)

def main():
    ioke = IokeShell()
    history = History()
    text = None
    line_num = 1
    prompt = None
    while True:
        try:
            text = get_input("{} > ".format(line_num), lexer=IokeLexer,
                history=history, completer=ioke_completer)
            if prompt is None:
                prompt = ioke.current_prompt
        except EOFError:
            break
        except KeyboardInterrupt:
            text = ""
        else:
            # TODO: diferentiate prompt (i = 0) and debug (i = 1)
            if text:
                ioke.execute(text)
                prompt = ioke.current_prompt
                print('echo> ', ioke.output)
                line_num += 1
    print("Goodbye")

if __name__ == '__main__':
    main()
