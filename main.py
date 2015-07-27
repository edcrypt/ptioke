from __future__ import unicode_literals
from __future__ import print_function
from prompt_toolkit.shortcuts import get_input
from prompt_toolkit.history import History
from prompt_toolkit.contrib.completers import WordCompleter
from pygments.lexers import IokeLexer

IOKE_VOCAB  = ['method'] # TODO

ioke_completer = WordCompleter(IOKE_VOCAB)

def main():
    history = History()
    line_num = 1
    while True:
        try:
            text = get_input("{} > ".format(line_num), lexer=IokeLexer,
                history=history, completer=ioke_completer)
        except Exception:
            break
        else:
            if text:
                print('=> ', text)
                line_num += 1
    print("Goodbye")

if __name__ == '__main__':
    main()
