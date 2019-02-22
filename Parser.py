import functools
from textwrap import indent
import Tokenizer


class reprwrapper(object):
    """
    function with custom repr when printed
    """

    def __init__(self, repr, func):
        self._repr = repr
        self._func = func
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kw):
        return self._func(*args, **kw)

    def __repr__(self):
        return self._repr(self._func)


def withrepr(reprfun):
    def _wrap(func):
        return reprwrapper(reprfun, func)
    return _wrap


class Success:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Success({self.value})"


class Failure:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Failure({self.value})"


class Parser:
    def __init__(self, grammar, cursor=0, length=None):
        self.grammar = {}
        self.cursor = cursor
        self.length = (len(grammar) - cursor
                       if not length else
                       length)

        """
        parse and store grammar rules
        """
        grammar_lines = grammar.strip().split("\n")
        grammar_stripped = map(str.strip, grammar_lines)
        grammar_nonempty = filter(lambda rule: ":" in rule, grammar_stripped)
        grammar = list(grammar_nonempty)

        for line in grammar:
            g_name, rule = line.split(":", 1)
            self.grammar[g_name] = rule

    def parse(self, tokens, debug=False):
        self.tokens = tokens

        self.eat("SOF", True)
        # return self.expr().value

        if debug:
            return self

        retval = self.SOF()
        assert isinstance(retval, Success), retval.value
        return retval.value

    # --- [ Parser functions ] --- #

    def peek(self):
        if (self.length <= 0):
            raise IndexError('index out of range')

        return self.tokens[self.cursor]

    def eat(self, token_type, shouldCall=False):
        """
        consume a token, return Failure if type does not match
        """
        @withrepr(lambda func: "Eat({token_type})".format(token_type=token_type))
        def call():
            token = self.peek()
            if token.type == token_type or token.value == token_type.strip("'"):
                self.cursor += 1
                return token
            else:
                return Failure(f"Unexpected token {token_type} got {self.peek()}")

        if shouldCall:
            return call()
        return call

    def rollback(self, distance):
        self.cursor -= distance
        if self.cursor < 0:
            self.cursor = 0

    @staticmethod
    def _returnResult(result):
        if isinstance(result, Failure):
            return result
        if isinstance(result, Success):
            return Success(result.value)
        return Success(result)

    @staticmethod
    def run(rule):
        if callable(rule):
            result = rule()
            return Parser._returnResult(result)
        else:
            return rule

    def pretty(self, ast, indent=0):
        for node in ast:
            if type(node) is list:
                self.pretty(node, indent + 2)
            else:
                print(" " * indent, node)

    # --- [ Commands ] --- #

    def Either(self, *sequence, shouldCall=False):
        """
        regex: (a | b | c | ...)
        """

        @withrepr(lambda func: "Either({sequence})".format(sequence=sequence))
        def call():
            for seq in sequence:
                start_pos = self.cursor

                result = self.run(seq)

                if isinstance(result, Failure):
                    self.rollback(self.cursor - start_pos)

                if isinstance(result, Success):
                    if result.value:
                        return result.value

            err = indent(result.value, " " * 4)
            return Failure(f"Either failed at position {self.cursor}, got error {{ \n { err } \n }}")

        if shouldCall:
            return call()
        return call

    def Sequence(self, *steps, shouldCall=False):
        """
        regex: (...)
        """
        @withrepr(lambda func: "Sequence({steps})".format(steps=steps))
        def call():
            results = []
            for step in steps:
                result = self.run(step)

                if isinstance(result, Failure):
                    err = indent(result.value, " " * 4)
                    return Failure(f"Sequence failed at position {self.cursor}, got error {{ \n { err } \n }}")

                if isinstance(result, Success):
                    if result.value:
                        if type(result.value) is list and len(result.value) == 1:
                            results += result.value
                        else:
                            results.append(result.value)

            return results

        if shouldCall:
            return call()
        return call

    def Optional(self, *steps, shouldCall=False):
        """
        regex: (...)?
        """
        @withrepr(lambda func: "Optional({steps})".format(steps=steps))
        def call():
            sequence = self.Sequence(*steps)

            start_pos = self.cursor

            result = self.run(sequence)

            if isinstance(result, Failure):
                self.rollback(self.cursor - start_pos)
                return None

            if isinstance(result, Success):
                return result.value

        if shouldCall:
            return call()
        return call

    def ZeroOrMore(self, *steps, shouldCall=False):
        """
        regex: (...)*
        """
        @withrepr(lambda func: "ZeroOrMore({steps})".format(steps=steps))
        def call():
            sequence = self.Sequence(*steps)
            results = []

            start_pos = self.cursor
            result = self.run(sequence)
            while not isinstance(result, Failure):
                if isinstance(result, Success):
                    results.append(result.value)

                start_pos = self.cursor
                result = self.run(sequence)

            self.rollback(self.cursor - start_pos)
            return results

        if shouldCall:
            return call()
        return call

    def OneOrMore(self, *steps, shouldCall=False):
        """
        regex: (...)+
        """
        @withrepr(lambda func: "OneOrMore({steps})".format(steps=steps))
        def call():
            sequence = self.Sequence(*steps)
            results = []

            start_pos = self.cursor
            result = self.run(sequence)
            while not isinstance(result, Failure):
                if isinstance(result, Success):
                    results.append(result.value)

                start_pos = self.cursor
                result = self.run(sequence)

            self.rollback(self.cursor - start_pos)

            if not results:
                err = indent(result.value, " " * 4)
                return Failure(f"OneOrMore failed at position {self.cursor}, got error {{ \n { err } \n }}")

            return results

        if shouldCall:
            return call()
        return call

    # --- [ Rules ] --- #

    def SOF(self):
        result = self.Either(
            self.funcdef,
            self.OneOrMore(
                self.stmt
            )
        )
        return self.run(result)

    def funcdef(self):
        result = self.Sequence(
            self.eat("'FUNCTION'"),
            self.eat("NAME"),
            self.parameter_clause,
            self.eat(":"),
            self.suite,
            self.return_stmt
        )
        # print("funcdef")
        return self.run(result)

    def return_stmt(self):
        result = self.Sequence(
            self.eat("'RETURN'"),
            self.Optional(self.test),
            self.eat(";")
        )
        # print("return_stmt")
        return self.run(result)

    def parameter_clause(self):
        result = self.Sequence(
            self.eat("("),
            self.Optional(self.parameters),
            self.eat(")")
        )
        # print("parameter_clause")
        return self.run(result)

    def parameters(self):
        result = self.Sequence(
            self.parameter,
            self.ZeroOrMore(
                self.eat(","),
                self.parameter
            )
        )
        # print("parameters")
        return self.run(result)

    def parameter(self):
        result = self.Sequence(
            self.eat("NAME")
        )
        # print("parameter")
        return self.run(result)

    def stmt(self):
        result = self.Either(
            self.simple_stmt,
            self.compound_stmt
        )
        # print("stmt")
        return self.run(result)

    def simple_stmt(self):
        result = self.Sequence(
            self.Either(
                self.call,
                self.assign
            ),
            self.eat(';')
        )
        # print("simple_stmt")
        return self.run(result)

    def assign(self):
        result = self.Sequence(
            self.eat("NAME"),
            self.Either(
                self.eat("'←'"),
                self.eat("'='")
            ),
            self.expr
        )
        # print("assign")
        return self.run(result)

    def call(self):
        result = self.Sequence(
            self.eat("NAME"),
            self.eat("("),
            self.expr,
            self.eat(")")
        )
        # print("call")
        return self.run(result)

    def compound_stmt(self):
        result = self.Either(
            self.if_stmt,
            self.while_stmt
        )
        # print("compound_stmt")
        return self.run(result)

    def if_stmt(self):
        result = self.Sequence(
            self.eat("'if'"),
            self.test,
            self.eat("then"),
            self.suite,
            self.ZeroOrMore(
                self.eat("'elif'"),
                self.test,
                self.eat("'then'"),
                self.suite
            ),
            self.Optional(
                self.eat("'else'"),
                self.suite
            ),
            self.eat("'fi'")
        )
        # print("if_stmt")
        return self.run(result)

    def while_stmt(self):
        result = self.Sequence(
            self.eat("'while'"),
            self.test,
            self.eat("then"),
            self.suite,
            self.eat("'done'")
        )
        # print("while_stmt")
        return self.run(result)

    def suite(self):
        result = self.Either(
            self.simple_stmt,
            self.OneOrMore(
                self.stmt
            )
        )
        # print("suite")
        return self.run(result)

    def test(self):
        result = self.Sequence(
            self.or_test
        )
        # print("test")
        return self.run(result)

    def or_test(self):
        result = self.Sequence(
            self.and_test,
            self.ZeroOrMore(
                self.eat('or'),
                self.and_test
            )
        )
        # print("or_test")
        return self.run(result)

    def and_test(self):
        result = self.Sequence(
            self.not_test,
            self.ZeroOrMore(
                self.eat('and'),
                self.not_test
            )
        )
        # print("and_test")
        return self.run(result)

    def not_test(self):
        result = self.Either(
            self.Sequence(
                self.eat('not'),
                self.not_test
            ),
            self.comparison
        )
        # print("not_test")
        return self.run(result)

    def comparison(self):
        result = self.Sequence(
            self.expr,
            self.ZeroOrMore(
                self.eat("COMPOP"),
                self.expr
            )
        )
        # print("comparison")
        return self.run(result)

    def expr(self):
        result = self.Sequence(
            self.term,
            self.ZeroOrMore(
                self.eat("ADDOP"),
                self.term
            )
        )
        # print("expr")
        return self.run(result)

    def term(self):
        result = self.Either(
            self.call,
            self.Sequence(
                self.factor,
                self.ZeroOrMore(
                    self.eat("MULTOP"),
                    self.factor
                )
            )
        )
        # print("term")
        return self.run(result)

    def factor(self):
        result = self.Either(
            self.call,
            self.Sequence(
                self.eat("("),
                self.expr,
                self.eat(")")
            ),
            self.power,
            self.atom
        )
        # print("factor")
        return self.run(result)

    def power(self):
        result = self.Sequence(
            self.atom,
            self.Optional(
                self.eat("POWOP"),
                self.factor
            )
        )
        # print("power")
        return self.run(result)

    def atom(self):
        result = self.Either(
            self.eat("NAME"),
            self.eat("NUMBER"),
            self.eat("STRING"),
            self.eat("'None'"),
            self.eat("'True'"),
            self.eat("'False'")
        )
        # print("atom")
        return self.run(result)
