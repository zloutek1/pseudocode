import re


class EBNF:
    def __init__(self, grammar):
        grammar = grammar.strip().split("\n")
        grammar = list(filter(lambda row: ":" in row, grammar))
        grammar = list(map(lambda row: list(map(str.strip, row.strip().split(":", 1))), grammar))
        grammar = list(filter(lambda rule: not rule[0].isupper(), grammar))

        self.grammar = grammar
        self.generate_rules()

    def generate_rules(self):
        for rule in self.grammar:
            print(rule)
