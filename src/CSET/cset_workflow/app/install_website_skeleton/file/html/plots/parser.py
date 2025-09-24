#!/usr/bin/env python3

"""Search query lexer and parser."""

import re
from collections.abc import Iterable
from enum import Flag, auto


class TT(Flag):
    """Type of token, as a bit flag."""

    WHITESPACE = auto()
    # Grouping.
    BEGIN_PARENTHESIS = auto()
    END_PARENTHESIS = auto()
    GROUPING = BEGIN_PARENTHESIS | END_PARENTHESIS
    # Facets
    FACET = auto()
    COLON = auto()
    # Operators.
    NOT = auto()
    NOT_EQUALS = auto()
    GREATER_THAN = auto()
    GREATER_THAN_OR_EQUALS = auto()
    LESS_THAN = auto()
    LESS_THAN_OR_EQUALS = auto()
    EQUALS = auto()
    OPERATOR = (
        NOT
        | GREATER_THAN
        | GREATER_THAN_OR_EQUALS
        | LESS_THAN
        | LESS_THAN_OR_EQUALS
        | NOT_EQUALS
        | EQUALS
    )
    # Combiners
    AND = auto()
    OR = auto()
    COMBINER = AND | OR
    # Literal value.
    LITERAL = auto()


class Token:
    """Token, possibly with a value."""

    kind: TT
    value: str | None

    def __init__(self, kind, value=None) -> None:
        self.kind = kind
        self.value = value

    def __str__(self) -> str:
        """Return str(self)."""
        if self.value is None:
            return self.kind.name
        else:
            return f"{self.kind.name}[{self.value}]"


def lexer(s) -> Iterable[Token]:
    """Lex input string."""
    token_specification = {
        TT.WHITESPACE: r"[ \t]+",
        TT.BEGIN_PARENTHESIS: r"\(",
        TT.END_PARENTHESIS: r"\)",
        TT.FACET: r"[a-z_\-]+[ \t]*:",
        TT.NOT_EQUALS: r"!=",
        TT.GREATER_THAN_OR_EQUALS: r"<=",
        TT.LESS_THAN_OR_EQUALS: r">=",
        TT.NOT: r"!",
        TT.GREATER_THAN: r"<",
        TT.LESS_THAN: r">",
        TT.EQUALS: r"=",
        TT.AND: r"and",
        TT.OR: r"or",
        TT.LITERAL: r"[^ \t\(\)]+",
    }
    token_regex = "|".join(
        f"(?P<{key.name}>{val})" for key, val in token_specification.items()
    )
    for match in re.finditer(token_regex, s, flags=re.IGNORECASE):
        assert match.lastgroup
        kind = getattr(TT, match.lastgroup)
        value = match.group()
        match kind:
            case TT.WHITESPACE:
                continue
            case TT.FACET:
                facet_match = re.fullmatch(r"([^ \t\(\)]+)[ \t]*:", value)
                assert facet_match
                yield Token(TT.LITERAL, facet_match.group(1))
                yield Token(TT.COLON)
            case TT.LITERAL:
                yield Token(kind, value)
            case _:
                yield Token(kind)


"""EBNF to implement:

query =
    expression

combiner =
    AND | OR

expression =
    condition | condition combiner? condition

condition =
    facet? ":" value | "(" expression ")"

facet =
    LITERAL

value =
    operator? LITERAL

operator =
    NOT | GREATER_THAN | GREATER_THAN_OR_EQUALS | LESS_THAN | LESS_THAN_OR_EQUALS | NOT_EQUALS | EQUALS
"""


def parser(tokens: Iterable[Token]):
    """Parse tokens into AST."""


query = "(histogram AND field : temperature) OR (time_series AND field:humidity) date:>= 2025-09-25T15:22Z"
tokens = list(lexer(query))
for token in tokens:
    print(token)

print("-" * 50)

ast = parser(tokens)
print(ast)
