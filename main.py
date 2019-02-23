
grammar = """
    SOF: funcdef | stmt

    funcdef: 'FUNCTION' NAME parameter_clause ':' suite return_stmt
    return_stmt: 'RETURN' [test] ';'

    parameter_clause: '(' [parameters] ')'
    parameters: parameter (',' parameter)*
    parameter: NAME

    suite: simple_stmt | stmt+

    stmt: simple_stmt | compound_stmt
    simple_stmt: (call | assign | expr) ';'

    assign: NAME ('←' | '=') expr
    call: NAME '(' expr ')'

    compound_stmt: if_stmt | while_stmt
    if_stmt: 'if' test 'then' suite ('elif' test 'then' suite)* ['else' suite] 'fi'
    while_stmt: 'while' test 'then' suite 'done'

    test: or_test
    or_test: and_test ('or' and_test)*
    and_test: not_test ('and' not_test)*
    not_test: 'not' not_test | comparison
    comparison: expr (COMPOP expr)*

    expr: term (ADDOP term)*
    term: call | factor (MULTOP factor)*
    factor: call | '(' expr ')' | power | atom
    power: atom [POWOP factor]

    atom: NAME | NUMBER | STRING | 'None' | 'True' | 'False'

    NAME: [a-zA-Z_][a-zA-Z0-9_]*
    NUMBER: ([0-9]*\.[0-9]+|[0-9]+)
    STRING: (\"|\')[a-zA-Z0-9]*(\"|\')
    COMPOP: (\=\=|\>\=|\<\=|\<\>|\!\=|\<|\>)
    POWOP: (\*\*)
    ADDOP: (\+|\-|\−)
    MULTOP: (\/\/|\*|\·|\/|\%)
    IGNORABLE: \s+
"""

"""
rules EBNF:
    <name>: <rule>
    <rule>: <option1> | <option2> | ... | <optionN>
    <rule>: <repeat0orMore>*
    <rule>: <repeat1orMore>+
    <rule>: [<optional>]
    <rule>: 'word'
    <rule>: <anotherRule>
    <rule>: (<group>)
    <rule>: <TERMINAL>
"""

program = """
  FUNCTION funkceG(x):
  if  x<0  then  x ← 0; fi
  if  x<14  then
    r ← funkceG(58−4·x)−9;
  else
    r ← 39;
  fi
  RETURN r;
"""

program = """
    if x < 0 and y < 0 then
        r = 5;
    elif 0 < x or 0 < y then
        r = 6;
    else
        r = 7;
    fi
"""

from EBNF import EBNF

from Tokenizer import Tokenizer
from Parser import Parser, Success
from Generator import Generator

from pprint import pprint

ebnf = EBNF(grammar)
tokenizer = Tokenizer(grammar)
tokens = tokenizer.tokenize(program)

parser = Parser(grammar)
ast = parser.parse(tokens)
# parser.pretty(ast)

from xml.etree.ElementTree import tostring
with open("output.xml", 'wb') as file:
    file.write(tostring(ast))


def unit_test(func, codes):
    for code in codes:
        parser = Parser(grammar).parse(Tokenizer(grammar).tokenize(code), debug=True)
        result = getattr(parser, func)()
        assert isinstance(result, Success) and parser.peek().type is "EOF", f"{func} got a failure with input {code} and result {result}"

    print(f"{func} passed unit test")


"""
unit_test('atom', codes=["a", "8", "\"Hello\"", "None", "True", "False"])
unit_test('power', codes=["5", "5 ** 2"])
unit_test('factor', codes=["(3*2)", "5", "5 ** 2"])
unit_test('expr', codes=["(3*2)/8-4+(9-4)"])

unit_test('comparison', codes=["5 < 4", "5 > 4", "5 == 4", "5 <= 4", "5 >= 4", "5 != 4"])
unit_test('not_test', codes=["not True"])
unit_test('and_test', codes=["True and False"])
unit_test('or_test', codes=["3 < 5 or x > 10 and True"])

unit_test('assign', codes=["x ← 5;"])
"""
