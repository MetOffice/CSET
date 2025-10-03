#!/usr/bin/env python3

"""Search query lexer and parser."""

import re
from collections.abc import Iterable, Sequence
from enum import Flag, auto
from typing import Callable, Literal


class TT(Flag):
    """Type of token, as a bit flag."""

    WHITESPACE = auto()
    # Grouping.
    BEGIN_PARENTHESIS = auto()
    END_PARENTHESIS = auto()
    GROUPING = BEGIN_PARENTHESIS | END_PARENTHESIS
    # Facets.
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
    # Combiners.
    AND = auto()
    OR = auto()
    NOT = auto()
    COMBINER = AND | OR | NOT
    # Literal value.
    LITERAL = auto()


class Token:
    """Token, possibly with a value."""

    kind: TT
    value: str

    def __init__(self, kind, value="") -> None:
        self.kind = kind
        self.value = value

    def __str__(self) -> str:
        """Return str(self)."""
        if self.value == "":
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
        # TODO: Consider using `-` instead of `!`, as that is what is used by GitHub and Danbooru.
        TT.NOT_IN: r"!",
        TT.GREATER_THAN: r"<",
        TT.LESS_THAN: r">",
        TT.EQUALS: r"=",
        TT.AND: r"\band\b",
        TT.OR: r"\bor\b",
        TT.NOT: r"\bnot\b",
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
    """Logically combine two Conditions with an AND."""

    def combined(d: dict) -> bool:
        return left(d) and right(d)

    return combined


def combiner_or(left: Condition, right: Condition) -> Condition:
    """Logically combine two Conditions with an OR."""

    def combined(d: dict) -> bool:
        return left(d) or right(d)

    return combined


def combiner_not(right: Condition) -> Condition:
    """Logically NOT a Condition."""

    def combined(d: dict) -> bool:
        return not right(d)

    return combined


def parse_condition(tokens: Sequence[Token]) -> tuple[int, Condition | None]:
    """Parse a condition from a stream of tokens.

    Arguments
    ---------
    tokens: Sequence[Token]
        Sequence of tokens, starting from the potential condition.

    Returns
    -------
    offset: int
        How many tokens were consumed by the condition. A value of 0 indicates
        it was not a condition.
    Condition | None
        The Condition function for this condition. None if there was not a
        condition.
    """
    if (
        # Just a value to search for.
        len(tokens) >= 1
        and tokens[0].kind == TT.LITERAL
        and (len(tokens) == 1 or tokens[1].kind != TT.COLON)
    ):
        return 1, create_condition(tokens[0].value)
    elif (
        # Value to search for with operator.
        len(tokens) >= 2
        and tokens[0].kind in TT.OPERATOR
        and tokens[1].kind == TT.LITERAL
    ):
        return 2, create_condition(tokens[1].value, operator=tokens[0].kind)
    elif (
        # Value to search for in facet.
        len(tokens) >= 3
        and tokens[0].kind == TT.LITERAL
        and tokens[1].kind == TT.COLON
        and tokens[2].kind == TT.LITERAL
    ):
        return 3, create_condition(tokens[2].value, facet=tokens[0].value)
    elif (
        # Value to search for in facet with operator.
        len(tokens) >= 4
        and tokens[0].kind == TT.LITERAL
        and tokens[1].kind == TT.COLON
        and tokens[2].kind in TT.OPERATOR
        and tokens[3].kind == TT.LITERAL
    ):
        return 4, create_condition(
            tokens[3].value, facet=tokens[0].value, operator=tokens[2].kind
        )
    else:
        # Not matched as a condition.
        return 0, None


def parse_grouped_expression(tokens: Sequence[Token]) -> int:
    """Parse a grouped expression from a stream of tokens.

    Arguments
    ---------
    tokens: Sequence[Token]
        Sequence of tokens, starting from the potential grouped expression.

    Returns
    -------
    offset: int
        How many tokens were consumed by the grouped expression. A value of 0
        indicates it was not a grouped expression.

    Raises
    ------
    ValueError
        If the parentheses are unmatched.
    """
    if len(tokens) < 2 or tokens[0].kind != TT.BEGIN_PARENTHESIS:
        return 0

    offset = 1
    depth = 1
    while depth > 0 and offset < len(tokens):
        match tokens[offset].kind:
            case TT.BEGIN_PARENTHESIS:
                depth += 1
            case TT.END_PARENTHESIS:
                depth -= 1
        offset += 1
    if depth != 0:
        raise ValueError("Unmatched parenthesis.")

    return offset


def parse_expression(tokens: Sequence[Token]) -> Condition:
    """Parse an expression into a single Condition function.

    Arguments
    ---------
    tokens: Sequence[Token]
        Sequence of tokens to parse.

    Returns
    -------
    Condition
        The condition represented by the tokens.

    Raises
    ------
    ValueError
        If the tokens do not form a valid expression.
    """
    print("Parsing tokens:", " ".join(str(t) for t in tokens))

    conditions: list[Condition | Literal[TT.AND] | Literal[TT.OR]] = []
    index = 0
    while index < len(tokens):
        # Accounts for Literals and Operators.
        offset, condition = parse_condition(tokens[index:])
        if offset > 0:
            index += offset
            conditions.append(condition)
            continue

        # Accounts for AND/OR.
        if tokens[index].kind in TT.COMBINER:
            conditions.append(tokens[index].kind)
            index += 1
            continue

        if tokens[index].kind == TT.NOT_IN:
            conditions.append(tokens[index].kind)
            index += 1
            continue

        # Accounts for parentheses.
        offset = parse_grouped_expression(tokens[index:])
        if offset > 0:
            # Recursively parse the grouped expression.
            inner_condition = parse_expression(tokens[index + 1 : index + offset - 1])
            conditions.append(inner_condition)
            index += offset
            continue

        raise ValueError(f"Unexpected token in expression: {tokens[index]}")

    return collapse_conditions(conditions)


# TODO: Change precedence so that implicit ands are evaluated with the same
# precedence as explicit ANDs. This is probably more useful/less surprising
# given what an OR is typically used for. It also matches the behaviour of other
# similar search systems, like GitHub or Danbooru.


def collapse_conditions(
    conditions: list[Condition | Literal[TT.AND] | Literal[TT.OR]],
) -> Condition:
    """Collapse a list of conditions and combiners into a single Condition.

    Pairs of conditions without an explicit combiner are treated as AND.

    The order of operations is:
        1. Evaluate NOTs first, left to right.
        2. Evaluate ANDs (explicit and implicit) second, left to right.
        3. Evaluate ORs third, left to right.

    Arguments
    ---------
    conditions: list[Condition | Literal[TT.AND] | Literal[TT.OR]]
        List of conditions and combiners.

    Returns
    -------
    Condition
        The collapsed condition that results from combining the conditions.

    Raises
    ------
    ValueError
        If the conditions list is empty or has unpaired combiners.
    """
    print("Combining conditions:", conditions)

    if not conditions:
        raise ValueError("No conditions to collapse.")

    combiners = (TT.AND, TT.OR, TT.NOT)

    # Evaluate NOTs first, left to right.
    if len(conditions) >= 2:
        collapsed_conditions = []
        index = 0
        while index < len(conditions):
            match conditions[index : index + 2]:
                case [TT.NOT, right] if right not in combiners:
                    collapsed_conditions.append(combiner_not(right))
                    index += 2
                case [left, *_] if left != TT.NOT:
                    collapsed_conditions.append(left)
                    index += 1
        conditions = collapsed_conditions

    # Evaluate ANDs second, left to right.
    if len(conditions) >= 3:
        collapsed_conditions = []
        index = 0
        while index < len(conditions):
            match conditions[index : index + 3]:
                case [left, TT.AND, right] if (
                    left not in combiners and right not in combiners
                ):
                    collapsed_conditions.append(combiner_and(left, right))
                    index += 3
                case [left, right, *_] if (
                    left not in combiners and right not in combiners
                ):
                    # TODO: Need this to loop.
                    collapsed_conditions.append(combiner_and(left, right))
                    index += 2
                case [left, *_] if left != TT.AND:
                    collapsed_conditions.append(left)
                    index += 1
        conditions = collapsed_conditions

    # Evaluate ORs third, left to right.
    if len(conditions) >= 3:
        collapsed_conditions = []
        index = 0
        while index < len(conditions):
            match conditions[index : index + 3]:
                case [left, TT.OR, right] if (
                    left not in combiners and right not in combiners
                ):
                    collapsed_conditions.append(combiner_or(left, right))
                    index += 3
                case [left, *_] if left != TT.OR:
                    collapsed_conditions.append(left)
                    index += 1
        conditions = collapsed_conditions

    # Verify we only have conditions at this point.
    if any(condition in combiners for condition in conditions):
        raise ValueError("Unprocessed combiner.")

    # Evaluate implicit ANDs third, left to right.
    collapsed_condition = conditions[0]
    for condition in conditions[1:]:
        collapsed_condition = combiner_and(collapsed_condition, condition)

    return collapsed_condition


# query = "(histogram AND field : temperature) OR (time_series AND field:humidity) date:>= 2025-09-25T15:22Z ((!foo))"
query = "temperature NOT(!foo)"
tokens = list(lexer(query))
for token in tokens:
    print(token)

print("-" * 50)

query_func = parse_expression(tokens)

print("-" * 50)

for diagnostic in [
    {
        "title": "temperature_histogram_foo",
        "field": "temperature",
        "date": "2025-10-02T23:09Z",
        "show": "NO",
    },
    {
        "title": "temperature_histogram",
        "field": "temperature",
        "date": "2025-10-02T23:09Z",
        "show": "YES",
    },
    {
        "title": "old_temperature_histogram",
        "field": "temperature",
        "date": "2021-10-02T23:09Z",
        "show": "NO",
    },
    {
        "title": "humidity_histogram",
        "field": "humidity",
        "date": "2025-10-02T23:09Z",
        "show": "NO",
    },
    {
        "title": "humidity_time_series",
        "field": "humidity",
        "date": "2025-10-02T23:09Z",
        "show": "YES",
    },
]:
    print(f"{query_func(diagnostic)}\t{diagnostic}")
