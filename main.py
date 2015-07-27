from __future__ import unicode_literals
from __future__ import print_function
from prompt_toolkit.shortcuts import get_input
from prompt_toolkit.history import History
from pygments.lexers import IokeLexer

def main():
    history = History()
    while True:
        try:
            text = get_input("> ", lexer=IokeLexer, history=history)
        except Exception:
            break
        else:
            print('You entered:', text)
    print("Goodbye")

if __name__ == '__main__':
    main()
