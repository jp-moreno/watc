#!/usr/bin/env python3

import argparse
from ply import lex

# List of token names
tokens = [
    'ID',
    'ASTERISK',  # *

    # 'DECIMAL',  # .

    'PLUS',  # +
    'MINUS',  # -
    'DIVIDE',  # /
    'MODULO',  # %

    'PLUSPLUS',  # ++
    'MINUSMINUS',  # --

    'EQ',  # =
    'TIMESEQ',  # *=
    'DIVIDEEQ',  # /=
    'MODULOEQ',  # %=
    'PLUSEQ',  # +=
    'MINUSEQ',  # -=

    'COMMA',  # ,
    'SEMICOL',  # ;

    'BANG',  # !
    'LPAREN',  # (
    'RPAREN',  # )
    'LBRACE',  # {
    'RBRACE',  # }
    'LBRACKET',  # [
    'RBRACKET',  # ]

    'GT',  # >
    'GE',  # >=
    'LT',  # <
    'LE',  # <=
    'EQOP',  # ==
    'NOTEQ',  # !=
    'OROP',  # ||
    'ANDOP',  # &&

    'REFERENCE',  # &

    'NUMBER',  # integer

    'CHARACTER',  # character
    'TEXT',  # string

]


reserved = {
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'for': 'FOR',

    'int': 'INT',
    'char': 'CHAR',

    'continue': 'CONTINUE',
    'break': 'BREAK',
    'return': 'RETURN',
    'null': 'NULL',
    'true': 'TRUE',
    'false': 'FALSE',
    'TRUE': 'TRUE_UPPER',
    'FALSE': 'FALSE_UPPER'
}

tokens += list(reserved.values())


class minic_lexer():
    t_ignore = ' \t'

    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_ASTERISK = r'\*'
    t_DIVIDE = r'/'
    t_MODULO = r'%'

    t_PLUSPLUS = r'\+\+'
    t_MINUSMINUS = r'\-\-'

    t_EQ = r'='
    t_TIMESEQ = r'\*='
    t_DIVIDEEQ = r'\/='
    t_MODULOEQ = r'%='
    t_PLUSEQ = r'\+='
    t_MINUSEQ = r'-='

    t_SEMICOL = r';'

    t_BANG = r'!'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    # Needs to be implemented in sprint2, since it depends on pointers
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'

    t_GT = r'>'
    t_GE = r'>='
    t_LT = r'<'
    t_LE = r'<='
    t_OROP = r'\|\|'
    t_EQOP = r'=='
    t_NOTEQ = r'!='
    t_ANDOP = r'&&'

    t_REFERENCE = r'\&'

    t_COMMA = ','

    t_CHARACTER = r'\'\w\''
    t_TEXT = r'\"\w+\"'

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = reserved.get(t.value, 'ID')  # Check for reserved words
        return t

    def t_NUMBER(self, t):
        r'[0-9]+'
        t.value = int(t.value)
        return t

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Build the lexer. DO NOT MODIFY
    def build(self, **kwargs):
        self.tokens = tokens
        self.lexer = lex.lex(module=self, **kwargs)

    # Test the output. DO NOT MODIFY
    def test(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            print(tok)


# Main function. DO NOT MODIFY
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Take in the miniC source code and perform lexical analysis.')
    parser.add_argument('FILE', help="Input file with miniC source code")
    args = parser.parse_args()
    try:
        f = open(args.FILE, 'r')
        file_data = f.read()
        f.close()
        m = minic_lexer()
        m.build()
        m.test(file_data)
    except FileNotFoundError:
        print("File not found, please provide a valid file")
        exit(1)
