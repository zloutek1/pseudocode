from collections import namedtuple
import re


class Lexer:
    def __init__(self, code=None, tokens=None, grammar=None):
        self.tokens = tokens
        self.grammar = grammar
        self.code = code

        if grammar is not None:
            self.get_keywords()

        if tokens is not None:
            self.get_token_types()

    def get_keywords(self, grammar=None):
        grammar = grammar if grammar is not None else self.grammar
        self.KEYWORDS = list(set(re.findall("\'([^']*)\'", grammar)))

    def get_token_types(self, tokens=None):
        tokens = tokens if tokens is not None else self.tokens
        self.TOKEN_TYPES = {}

        tokens = tokens.strip().split("\n")
        for token in tokens:
            if ":" in token:
                name, reg = token.strip().split(":", 1)
                self.TOKEN_TYPES[name.strip()] = reg.strip()

    def tokenize(self, code=None):
        code = code if code is not None else self.code
        tokens = []

        while len(self.code) != 0:
            token = self.tokenize_one_token()
            if token.name != "IGNORABLE":
                tokens.append(token)
            code = code.strip()
        return tokens

    def tokenize_one_token(self):
        def slashed(text):
            return "".join([letter
                            if letter.isalpha() else
                            "\\" + letter
                            for letter in text])

        for (tokenType, reg) in self.TOKEN_TYPES.items():
            reg = "\A({reg})".format(reg=reg)
            match = re.search(reg, self.code)
            if match is not None:
                value = match.group(1)
                self.code = self.code[len(value):]
                return Token(tokenType, value)

        for keyword in self.KEYWORDS:
            reg = "\A({reg})".format(reg=slashed(keyword))
            match = re.search(reg, self.code)
            if match is not None:
                value = match.group(1)
                self.code = self.code[len(value):]
                return Token("KEYWORD", value)

        raise RuntimeError("Couldn't match token on {}".format(self.code))


Token = namedtuple("Token", ("name", "value"))
