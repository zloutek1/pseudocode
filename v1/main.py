
grammar = """
    SOF: funcdef | stmt

    funcdef: 'FUNCTION' NAME parameter_clause ':' suite return_stmt
    return_stmt: 'RETURN' [test] ';'

    parameter_clause: '(' [parameters] ')'
    parameters: parameter (',' parameter)*
    parameter: NAME

    stmt: simple_stmt | compound_stmt
    simple_stmt: assign

    assign: NAME '←' expr

    compound_stmt: if_stmt | while_stmt | funcdef
    if_stmt: 'if' test ':' suite ('elif' test ':' suite)* ['else' ':' suite] 'fi'
    while_stmt: 'while' test ':' suite ['else' ':' suite] 'done'

    suite: simple_stmt | stmt+

    test: or_test
    or_test: and_test ('or' and_test)*
    and_test: not_test ('and' not_test)*
    not_test: 'not' not_test | comparison
    comparison: expr (COMPOP expr)*

    expr: term (ADDOP term)*
    term: factor (MULTOP factor)*
    factor: ('+' | '-' | '−') atom | power
    power: atom [POWOP factor]

    atom: NAME | NUMBER | STRING | 'None' | 'True' | 'False'
"""

"""
comp_op: '<' | '>' | '==' | '>=' | '<=' | '<>' | '!='
expr: term (('+' | '-' | '−') term)*
term: factor (('*' | '·' | '/' | '%' | '//') factor)*
factor: ('+' | '-' | '−') factor | power
power: atom ['**' factor]
"""

tokens = """
    NAME: [a-zA-Z_][a-zA-Z0-9_]*
    NUMBER: ([0-9]*\.[0-9]+|[0-9]+)
    STRING: (\"|\')[a-zA-Z0-9]*(\"|\')
    COMPOP: (\<|\>|\=\=|\>\=|\<\=|\<\>|\!\=)
    ADDOP: (\+|\-|\−)
    MULTOP: (\*|\·|\/|\%|\/\/)
    POWOP: (\*\*)
    IGNORABLE: \s+
"""

program1 = """
  FUNCTION funkceG(x):
  if  x<0  then  x ← 0;
  if  x<14  then
    r ← funkceG(58−4·x)−9;
  else
    r ← 39;
  fi
  RETURN r;
"""

program = """
   3+2
"""

from Lexer import *
from Parser import *

lexer = Lexer(program1, tokens, grammar)
Parser(lexer, grammar)
