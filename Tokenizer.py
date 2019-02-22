import re


class Token:
    def __init__(self, _type, _value):
        self.type = _type
        self.value = _value

    def __str__(self):
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()


class Tokenizer:
    def __init__(self, grammar):
        self.terminals = {}
        self.keywords = set()

        grammar_lines = grammar.strip().split("\n")
        grammar_stripped = map(str.strip, grammar_lines)
        grammar_nonempty = filter(lambda rule: ":" in rule, grammar_stripped)
        grammar = list(grammar_nonempty)

        for line in grammar:
            t_name, rule = line.split(":", 1)
            if t_name.isupper():
                self.terminals[t_name] = "\A({rule})".format(rule=rule.strip())

            else:
                keywords = re.findall("\'([^\']+)\'", rule)
                for keyword in keywords:
                    reg = "\A({rule})".format(rule=keyword if keyword.isalpha() else "\\" + keyword)
                    self.keywords.add(('KEYWORD', reg))

    def tokenize(self, code):
        self.code = code
        tokens = []

        while len(self.code) != 0:
            token = self.tokenize_one_token()
            if token.type != "IGNORABLE":
                tokens.append(token)
            self.code = self.code.strip()

        return [Token("SOF", "SOF")] + tokens + [Token("EOF", None)]

    def tokenize_one_token(self):
        for (tokenType, reg) in tuple(self.keywords) + tuple(self.terminals.items()):
            match = re.search(reg, self.code)
            if match is not None:
                value = match.group(1)
                self.code = self.code[len(value):]
                return Token(tokenType, value)

        raise RuntimeError("Couldn't match token on {}".format(self.code))
