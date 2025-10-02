#!/usr/bin/env python3

"""Search query lexer and parser."""

import re
from collections.abc import Iterable, Sequence
from enum import Flag, auto
from typing import Callable


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
    IN = auto()
    NOT_IN = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    GREATER_THAN = auto()
    GREATER_THAN_OR_EQUALS = auto()
    LESS_THAN = auto()
    LESS_THAN_OR_EQUALS = auto()
    OPERATOR = (
        IN
        | NOT_IN
        | EQUALS
        | NOT_EQUALS
        | GREATER_THAN
        | GREATER_THAN_OR_EQUALS
        | LESS_THAN
        | LESS_THAN_OR_EQUALS
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
            assert self.kind.name, "Token always has a name."
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
        TT.NOT_IN: r"!",
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

expression =
    condition | condition combiner? expression | "(" expression ")"

combiner =
    AND | OR

condition =
    facet? operator? value

facet =
    LITERAL ":"

value = LITERAL

operator =
    NOT | GREATER_THAN | GREATER_THAN_OR_EQUALS | LESS_THAN | LESS_THAN_OR_EQUALS | NOT_EQUALS | EQUALS
"""

# Python 3.12 syntax for type alias uses the `type` keyword.
# type Classifier = Callable[[dict], bool]
Condition = Callable[[dict[str, str]], bool]


def create_condition(
    value: str, facet: str = "title", operator: TT = TT.IN
) -> Condition:
    """Create a condition.

    Arguments
    ---------
    value: str
        The value to check for within the facet.
    facet: str
        The facet to check.
    operator: TT
        The operation to check with. One of the values in TT.OPERATOR.

    Returns
    -------
    Condition
        A function implementing the condition. It may raise a KeyError if the
        facet is not present, so calling code should capture that.
    """
    match operator:
        case TT.IN:

            def condition(d: dict[str, str]) -> bool:
                return value in d[facet]
        case TT.NOT_IN:

            def condition(d: dict[str, str]) -> bool:
                return value not in d[facet]
        case TT.EQUALS:

            def condition(d: dict[str, str]) -> bool:
                return value == d[facet]
        case TT.NOT_EQUALS:

            def condition(d: dict[str, str]) -> bool:
                return value != d[facet]
        case TT.GREATER_THAN:

            def condition(d: dict[str, str]) -> bool:
                return value > d[facet]
        case TT.GREATER_THAN_OR_EQUALS:

            def condition(d: dict[str, str]) -> bool:
                return value >= d[facet]
        case TT.LESS_THAN:

            def condition(d: dict[str, str]) -> bool:
                return value < d[facet]
        case TT.LESS_THAN_OR_EQUALS:

            def condition(d: dict[str, str]) -> bool:
                return value <= d[facet]
        case _:
            raise ValueError(f"Invalid operator: {operator}")
    return condition


def combiner_and(left: Condition, right: Condition) -> Condition:
    """Logically combine two Condition with an AND."""

    def combined(d: dict) -> bool:
        return left(d) and right(d)

    return combined


def combiner_or(left: Condition, right: Condition) -> Condition:
    """Logically combine two Condition with an OR."""

    def combined(d: dict) -> bool:
        return left(d) or right(d)

    return combined


def parse_condition(tokens: Sequence[Token]) -> tuple[int, Condition | None]:
    """Parse a condition from a stream of tokens.

    Arguments
    ---------
    tokens: list[Token]
        List of tokens, starting from the potential condition.

    Returns
    -------
    offset: int
        How many tokens were consumed by the condition. A value of 0 indicates
        it was not a condition.
    Condition | None
        The Condition function for this condition. None if there was not a
        condition.
    """
    if len(tokens) == 1:
        if tokens[0].kind == TT.LITERAL:
            assert tokens[0].value, "Literal tokens always have a value."
            return 1, create_condition(tokens[0].value)
    elif len(tokens) > 1:
        if tokens[0].kind in TT.OPERATOR and tokens[1].kind == TT.LITERAL:
            assert tokens[1].value, "Literal tokens always have a value."
            return 2, create_condition(tokens[1].value, operator=tokens[0].kind)
        elif tokens[0].kind == TT.LITERAL and tokens[1].kind == TT.COLON:
            facet = tokens[0].value
            assert facet, "Literal tokens always have a value."
            if tokens[2].kind in TT.OPERATOR and tokens[3].kind == TT.LITERAL:
                assert tokens[3].value, "Literal tokens always have a value."
                return 4, create_condition(
                    tokens[3].value, facet=facet, operator=tokens[2].kind
                )
            elif tokens[2].kind == TT.LITERAL:
                assert tokens[2].value, "Literal tokens always have a value."
                return 3, create_condition(tokens[2].value, facet=facet)
    # Not matched as a condition.
    return 0, None


def parser(tokens: list[Token]):
    """Parse tokens into AST."""
    index = 0
    while index < len(tokens):
        token = tokens[index]
        match token.kind:
            # case TT.BEGIN_PARENTHESIS:
            #     collected = []
            #     index += 1
            #     token = tokens[index]
            #     while token != TT.END_PARENTHESIS:
            #         collected.append(token)
            #         index += 1
            #         token = tokens[index]

            case [TT.LITERAL, TT.COLON]:
                pass

            case TT.OPERATOR:
                pass

            case _:
                raise ValueError("Unknown token.")


query = "(histogram AND field : temperature) OR (time_series AND field:humidity) date:>= 2025-09-25T15:22Z ((!foo))"
tokens = list(lexer(query))
for token in tokens:
    print(token)

print("-" * 50)

ast = parser(tokens)
print(ast)
