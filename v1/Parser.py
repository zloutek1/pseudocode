from collections import namedtuple
import re
from textwrap import indent, dedent
from types import MethodType


class ParseError(Exception):
    pass


class EBNF:
    def __init__(self, tokens, grammar):
        self.grammar = grammar
        self.tokens = tokens
        self.tokenIndex = 0

        self.ast = []
        self.functions = {}

        rules = re.split("\s*\n+\s*", grammar.strip())
        for rule in rules:
            head, body = re.split("\:\s*", rule, 1)
            self.functions[head] = body

        for head in self.functions:
            body = self.functions[head]
            source = self._convert2source(head, body)
            eval(compile(source, '<string>', 'exec'))

            func = locals()[head]
            setattr(self, head, MethodType(func, self))

    def _convert2source(self, function_name, body, start_indent=0):
        actions = []

        """
        if function_name:
            source = dedent(\"""
                def {function_name}(self):
                    print('PARSING {function_name}')
                    actions = []

                    {body}

                    print('RETURNING', actions)
                    return actions
            \""").strip()
        else:
            source = ""

        alternative_block = dedent(\"""
            backtrack_by = 0
            try:
            {alternative_code}
            except ParseError:
                self.backtrack(backtract_by)
        \""").strip()

        function_call = dedent(\"""
            print('CALLING', {name})
            retval = self.{name}()
            actions.append(retval)
        \""").strip()

        eat_string = dedent(\"""
            self.eat({string})
            print('EATING', {string})
            actions.append(terminal)
            backtrack_by += 1
        \""").strip()

        eat_terminal = dedent(\"""
            terminal = self.eat({terminal})
            print('EATING', {terminal})
            actions.append(terminal)
            backtrack_by += 1
        \""").strip()

        repeating_block_plus = dedent(\"""
            {code}
            while True:
                try:
            {code2}
                except ParseError:
                    self.backtrack(backtrack_by)
                    break
        \""").strip()

        repeating_block_star = dedent(\"""
            while True:
                try:
            {code2}
                except ParseError:
                    self.backtrack()
                    break
        \""").strip()

        optional_block = dedent(\"""
            try:
            {code1}
            except ParseError:
                self.backtrack(backtrack_by)
        \""").strip()

        function_body = ""
        alternatives = self.split(body, "|", skipGroups=True)
        for altindex, alternative in enumerate(alternatives):

            alternative_code = ""
            parts = self.split(alternative, " ", skipGroups=True)
            for part in parts:

                if part in self.functions:
                    alternative_code += function_call.format(name=part) + "\n"

                elif self.isString(part):
                    alternative_code += eat_string.format(string=part) + "\n"

                elif self.isTerminal(part):
                    alternative_code += eat_terminal.format(terminal=part) + "\n"

                elif self.isRepeatPlus(part):
                    code = self._convert2source(None, part[:-1])
                    alternative_code += repeating_block_plus.format(code=code, code2=indent(code, " " * 4 * 2)) + "\n"

                elif self.isRepeatStar(part):
                    code = self._convert2source(None, part[:-1])
                    alternative_code += repeating_block_star.format(code=code, code2=indent(code, " " * 4 * 2)) + "\n"

                elif self.isGroup(part):
                    code = self._convert2source(None, part[1:-1])
                    alternative_code += code + "\n"

                elif self.isOptional(part):
                    code = self._convert2source(None, part[1:-1])
                    alternative_code += optional_block.format(code1=indent(code, " " * 4 * 1)) + "\n"

                else:
                    raise NotImplementedError(part)

            function_body += indent(
                alternative_block.format(
                    alternative_code=indent(alternative_code, " " * 4)),
                " " * 4) + "\n\n"

        source_code = source.format(function_name=function_name, body=function_body.strip())
        print(source_code)
        return source_code
        """

        if function_name:
            source = (f"def {function_name}(self):\n" +
                      # f"    print('PARSING {function_name}')\n" +
                      f"    actions=[]\n")
        else:
            source = (f"")

        alternatives = self.split(body, "|", skipGroups=True)
        for altindex, alternative in enumerate(alternatives):

            alternative_block = ""
            parts = self.split(alternative, " ", skipGroups=True)
            for part in parts:
                if part in self.functions:
                    alternative_block += f"actions.append(self.{part}())\n"

                elif self.isString(part):
                    alternative_block += f"self.eat(\"{part}\")\n"
                    # alternative_block += f"print('eating', \"{part}\")\n"

                elif self.isTerminal(part):
                    alternative_block += f"actions.append(self.eat(\"{part}\"))\n"
                    # alternative_block += f"print('eating', \"{part}\")\n"

                elif self.isRepeatPlus(part):
                    code = self._convert2source(None, part[:-1])
                    code2 = indent(code, "        ")
                    alternative_block += (f"{code}\n" +
                                          f"while True:\n" +
                                          f"    try:\n" +
                                          f"{code2}\n" +
                                          f"    except ParseError:\n" +
                                          # f"        print('repeat+ ParseError')\n" +
                                          f"        break\n")

                elif self.isRepeatStar(part):
                    code = indent(self._convert2source(None, part[:-1]), "        ")
                    alternative_block += (f"while True:\n" +
                                          f"    try:\n" +
                                          f"{code}\n" +
                                          f"    except ParseError:\n" +
                                          # f"        print('{function_name}: repeat* ParseError')\n" +
                                          f"        break\n")

                elif self.isGroup(part):
                    code = self._convert2source(None, part[1:-1])
                    alternative_block += f"{code}"

                elif self.isOptional(part):
                    code = indent(self._convert2source(None, part[1:-1]), "    ")
                    alternative_block += (f"try:\n" +
                                          f"{code}\n" +
                                          f"except ParseError:\n" +
                                          # f"    print('optional ParseError')\n" +
                                          f"    pass\n")

                else:
                    actions.append(("other", part))
                    raise NotImplementedError(part)

            if len(alternatives) > 1:
                alternative_block = indent(alternative_block, " " * 4)
                alt_code = (f"try:\n" +
                            f"{alternative_block}\n" +
                            f"except ParseError:\n" +
                            # f"    print(\"alternative {alternative} ParseError\")\n" +
                            (f"    pass\n"
                             if altindex != len(alternatives) - 1 else
                             f"    raise ParseError('alternative end')\n"))

                alt_code = indent(alt_code, " " * 4 * (altindex))
            else:
                alt_code = alternative_block

            source += indent(alt_code, " " * 4)

        if function_name:
            # source += f"    print(\"{function_name}: RETURNING\", actions)\n"
            source += f"    return self.flatten(actions)\n"

        return dedent(source)

    def isTerminal(self, rule):
        return rule.isupper()

    def isString(self, rule):
        return bool(re.match("[\"\'].+[\"\']", rule))

    def isRepeatStar(self, rule):
        return rule.endswith("*")

    def isRepeatPlus(self, rule):
        return rule.endswith("+")

    def isGroup(self, rule):
        return rule.startswith("(") and rule.endswith(")")

    def isOptional(self, rule):
        return rule.startswith("[") and rule.endswith("]")

    def peek(self):
        if self.tokenIndex < len(self.tokens):
            return self.tokens[self.tokenIndex]

    def eat(self, tokenValue):
        peekValue = self.peek()
        if peekValue:
            if peekValue.name == tokenValue or peekValue.value == tokenValue.strip("'"):
                retval = peekValue
                self.tokenIndex += 1
                return retval
            else:
                raise ParseError(f"Exppected {tokenValue} but got {self.peek()}")
        else:
            raise ParseError(f"EOS")

    def flatten(self, array):
        if len(array) == 1 and type(array) is list:
            return array[0]
        return array

    def backtrack(self, backtrack_by):
        self.tokenIndex -= backtrack_by

    @staticmethod
    def split(text, char, skipGroups=False):
        separated = []
        start, end, brack_depth = 0, 0, 0
        inString = False

        for letter in text:
            if skipGroups:
                if letter in ("'", '"'):
                    inString = not inString

                if letter in ('(', '[', '{') and not inString:
                    brack_depth += 1

                elif letter in (')', ']', '}') and not inString:
                    brack_depth -= 1

            if brack_depth == 0 and letter == char:
                separated.append(text[start:end].strip())
                start = end + 1

            end += 1
        else:
            separated.append(text[start:end].strip())

        return separated


class Parser:
    def __init__(self, lexer, grammar=None):
        self.lexer = lexer

        self.tokens = lexer.tokenize()
        self.grammar = EBNF(self.tokens, grammar)
        self.tokenIndex = 0

        print(self.grammar.SOF())


"""


class Parser:
    def __init__(self, lexer, grammar=None):
        self.lexer = lexer

        self.tokens = lexer.tokenize()
        self.grammar = grammar
        self.tokenIndex = 0

        if grammar is not None:
            self.parse()

    def parse(self, grammar=None):
        grammar = grammar if grammar is not None else self.grammar

        self.rule_list = self.get_rule_list()
        start_rule = 'funcdef'
        self.parse_rule(start_rule)

    def parse_rule(self, rule_name):
        rule = self.rule_list[rule_name]
        print()
        print("PARSING", rule_name, "::=", rule)

        options = self.split_rule(rule, char="\|")
        print("OPTIONS", options)
        for option in options:
            print("option - ", option)
            separated = self.split_rule(option, char=" ")
            print("     SEPARATED", separated)
            for part in separated:
                self.parse_part(part)

    def parse_part(self, part):
        # is rule_name
        if part in self.rule_list:
            print("parse", part)
            self.parse_rule(part)

        # is string
        if part.startswith("'") and part.endswith("'"):
            print("consume", part)

        # is group
        if self.is_group(part):
            # is repeating 1-more ()+
            if part.endswith("+"):
                self.parse_rule(part[1:-1])
                while True:
                    try:
                        self.parse_rule(part[1:-1])
                    except ParseError:
                        break

            # is bool ()?
            if part.endswith("?"):
                try:
                    self.parse_rule(part[1:-1])
                except ParseError:
                    pass

            # is repeating 0-more ()*
            if part.endswith("*"):
                while True:
                    try:
                        self.parse_rule(part[1:-1])
                    except ParseError:
                        break

        # is optional
        if self.is_optional(part):
            print("optional", part)

    def split_rule(self, rule, char):
        groups = []
        start_index, end_index = 0, 0
        bracket_indexes = self.find_brackets(rule)

        if len(bracket_indexes) == 0:
            return re.split("\s*" + char + "\s*", rule)

        bracket_index = 0
        (b_start, b_end) = bracket_indexes[bracket_index]
        while end_index < len(rule):
            if end_index == b_start:
                end_index = b_end
                bracket_index += 1

                if bracket_index < len(bracket_indexes):
                    (b_start, b_end) = bracket_indexes[bracket_index]

            print(end_index, rule[end_index], rule[end_index] == char)
            if rule[end_index] == char:
                groups.append(rule[start_index: end_index].strip())
                start_index = end_index + 1

            end_index += 1
        else:
            groups.append(rule[start_index: end_index].strip())

        return groups

    def is_group(self, rule):
        return bool(re.search("\(.*\)[\+\*\?]?", rule))

    def is_optional(self, rule):
        return bool(re.search("\[.*\][\+\*]?", rule))

    def peek(self):
        return self.tokens[self.tokenIndex]

    def eat(self, tokenValue):
        if self.peek().name == tokenValue or self.peek().value == tokenValue:
            retval = self.peek()
            self.tokenIndex += 1
            return retval
        else:
            raise ParseError(f"Exppected {tokenValue} but got {self.peek()}")

    def next(self):
        tokenType = self.peek()
        self.eat(tokenType)
        return tokenType

    def get_rule_list(self, grammar=None):
        grammar = grammar if grammar is not None else self.grammar

        rule_list = {}
        rules = grammar.strip().split("\n")
        for rule in rules:
            if ":" in rule:
                name, rule = rule.strip().split(":", 1)
                rule = self._fix_left_recursion(name, rule)
                rule_list[name] = rule.strip()

        return rule_list

    def _fix_left_recursion(self, rule_name, rule):
        # TODO: no need to fix this yet
        return rule

    @staticmethod
    def find_brackets(text):
        indexes = []
        start_index, end_index = 0, 0
        depth = 0
        open_brackets, close_brackets = ("(", "[", "{"), (")", "]", "}")
        bracket_additional = ("*", "+")

        while end_index < len(text):
            char_at = text[end_index]

            if char_at in open_brackets:
                if depth == 0:
                    start_index = end_index

                depth += 1

            if char_at in close_brackets:
                depth -= 1

                if depth == 0:
                    if text[end_index] in bracket_additional:
                        end_index += 1
                    indexes.append((start_index, end_index))

            end_index += 1

        return indexes
"""
