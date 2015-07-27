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

def main():
    ioke = pexpect.spawnu(IOKE)
    history = History()
    line_num = 1
    i = None
    while True:
        try:
            text = get_input("{} > ".format(line_num), lexer=IokeLexer,
                history=history, completer=ioke_completer)
            if i is None:
                i = ioke.expect([IOKE_PROMPT, IOKE_DEBUG])
        except EOFError:
            break
        except KeyboardInterrupt:
            text = ""
        else:
            # TODO: diferentiate prompt (i = 0) and debug (i = 1)
            if text:
                ioke.sendline(text)
                i = ioke.expect([IOKE_PROMPT, IOKE_DEBUG])
                print('echo> ', ioke.before)
                # TODO: Parse prints and +> (result)
                line_num += 1
    print("Goodbye")

if __name__ == '__main__':
    main()
