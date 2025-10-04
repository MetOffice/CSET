#!/usr/bin/env python3

"""Search query lexer and parser.

EBNF to implement:

query =
    expression

expression =
    condition | condition combiner? expression | NOT expression | "(" expression ")"

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

import re
from collections.abc import Callable, Iterable
from enum import Enum, auto
from typing import Literal


class Combiner(Enum):
    """Enum of combiners."""

    NOT = auto()
    AND = auto()
    OR = auto()


class Operator(Enum):
    """Enum of operators."""

    IN = auto()
    NOT_IN = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    GREATER_THAN = auto()
    GREATER_THAN_OR_EQUALS = auto()
    LESS_THAN = auto()
    LESS_THAN_OR_EQUALS = auto()


class Parenthesis(Enum):
    """Enum of parenthesis."""

    BEGIN = auto()
    END = auto()


class LexOnly(Enum):
    """Enum of tokens converted to richer types during lexing."""

    WHITESPACE = auto()
    FACET = auto()
    LITERAL = auto()


class LiteralToken:
    """A literal value."""

    value: str

    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        """Return str(self)."""
        return f"LiteralToken[{self.value}]"

    def __repr__(self) -> str:
        """Return repr(self)."""
        return f"LiteralToken({repr(self.value)})"


class Facet:
    """A facet value."""

    value: str

    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        """Return str(self)."""
        return f"Facet[{self.value}]"

    def __repr__(self) -> str:
        """Return repr(self)."""
        return f"Facet({repr(self.value)})"


Token = LiteralToken | Facet | Parenthesis | Combiner | Operator


def lexer(s: str) -> Iterable[Token]:
    """Lex input string into tokens."""
    token_spec = {
        Parenthesis.BEGIN: r"\(",
        Parenthesis.END: r"\)",
        Operator.GREATER_THAN_OR_EQUALS: r"<=",
        Operator.GREATER_THAN: r"<",
        Operator.LESS_THAN_OR_EQUALS: r">=",
        Operator.LESS_THAN: r">",
        Operator.NOT_EQUALS: r"!=",
        Operator.EQUALS: r"=",
        Operator.NOT_IN: r"!",
        Combiner.NOT: r"\bnot\b",
        Combiner.AND: r"\band\b",
        Combiner.OR: r"\bor\b",
        LexOnly.WHITESPACE: r"[ \t]+",
        LexOnly.FACET: r"[a-z_\-]+[ \t]*:",
        LexOnly.LITERAL: r"[^ \t\(\)]+",  # Should we support quoted literals?
    }
    token_regex = "|".join(
        f"(?P<{str(key).replace('.', '_')}>{val})" for key, val in token_spec.items()
    )
    token_name_mapping = {str(key).replace(".", "_"): key for key in token_spec.keys()}
    for match in re.finditer(token_regex, s, flags=re.IGNORECASE):
        # Get the Enum object from token_spec matching the capture group name.
        assert match.lastgroup, "match.lastgroup cannot be None."
        kind = token_name_mapping[match.lastgroup]
        value = match.group()
        match kind:
            case None:
                raise ValueError("Oh no!")
            case LexOnly.WHITESPACE:
                continue
            case LexOnly.FACET:
                facet_name = value.rstrip(" \t:")
                yield Facet(facet_name)
            case LexOnly.LITERAL:
                yield LiteralToken(value)
            case _:
                yield kind


class Condition:
    """A condition."""

    func: Callable

    def __init__(
        self,
        value: LiteralToken | Callable,
        facet: Facet = Facet("title"),  # noqa: B008
        operator: Operator = Operator.IN,
    ):
        """Create a condition.

        Arguments
        ---------
        value: str | Callable
            The value to check for within the facet. May also be a callable to
            determine this, in which case other arguments are ignored.
        facet: Facet, optional
            The facet to check. Defaults to title.
        operator: Operator, optional
            The operation to check with. One of the values of the Operator enum.
            Defaults to IN.

        Returns
        -------
        Condition
            A function implementing the condition. It may raise a KeyError if
            the facet is not present, so calling code should capture that.
        """
        if callable(value):
            self.func = value
            return

        v = value.value
        f = facet.value

        match operator:
            case Operator.IN:

                def condition(d: dict[str, str]) -> bool:
                    return v in d[f]
            case Operator.NOT_IN:

                def condition(d: dict[str, str]) -> bool:
                    return v not in d[f]
            case Operator.EQUALS:

                def condition(d: dict[str, str]) -> bool:
                    return v == d[f]
            case Operator.NOT_EQUALS:

                def condition(d: dict[str, str]) -> bool:
                    return v != d[f]
            case Operator.GREATER_THAN:

                def condition(d: dict[str, str]) -> bool:
                    return v > d[f]
            case Operator.GREATER_THAN_OR_EQUALS:

                def condition(d: dict[str, str]) -> bool:
                    return v >= d[f]
            case Operator.LESS_THAN:

                def condition(d: dict[str, str]) -> bool:
                    return v < d[f]
            case Operator.LESS_THAN_OR_EQUALS:

                def condition(d: dict[str, str]) -> bool:
                    return v <= d[f]
            case _:
                raise ValueError(f"Invalid operator: {operator}")

        self.func = condition

    def __repr__(self) -> str:
        """Return repr(self)."""
        return f"<Condition {hex(id(self))}>"

    def __call__(self, d: dict[str, str]) -> bool:
        """Implement self(d)."""
        return self.func(d)

    def __and__(self, other):
        """Implement self & other."""
        if not isinstance(other, Condition):
            return NotImplemented

        def combined(d: dict[str, str]) -> bool:
            return self(d) and other(d)

        return Condition(combined)

    def __or__(self, other):
        """Implement self | other."""
        if not isinstance(other, Condition):
            return NotImplemented

        def combined(d: dict[str, str]) -> bool:
            return self(d) or other(d)

        return Condition(combined)

    def __invert__(self):
        """Implement ~self."""

        def combined(d: dict[str, str]) -> bool:
            return not self(d)

        return Condition(combined)


def parse_grouped_expression(tokens: list[Token]) -> tuple[int, Condition | None]:
    """Parse a grouped expression from a stream of tokens.

    Arguments
    ---------
    tokens: list[Token]
        List of tokens, starting from the potential grouped expression.

    Returns
    -------
    offset: int
        How many tokens were consumed by the grouped expression. A value of 0
        indicates it was not a grouped expression.
    Condition | None
        The Condition function for this expression. None if there was not a
        grouped expression.

    Raises
    ------
    ValueError
        If the parentheses are unmatched.
    """
    if len(tokens) < 2 or tokens[0] != Parenthesis.BEGIN:
        return 0, None
    offset = 1
    depth = 1
    while depth > 0 and offset < len(tokens):
        match tokens[offset]:
            case Parenthesis.BEGIN:
                depth += 1
            case Parenthesis.END:
                depth -= 1
        offset += 1
    if depth != 0:
        raise ValueError("Unmatched parenthesis.")
    # Recursively parse the grouped expression.
    inner_expression = parse_expression(tokens[1 : offset - 1])
    return offset, inner_expression


def parse_condition(tokens: list[Token]) -> tuple[int, Condition | None]:
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
    match tokens[:3]:
        case [lt, *_] if isinstance(lt, LiteralToken):
            # Just a value to search for.
            return 1, Condition(lt)
        case [op, lt, *_] if isinstance(op, Operator) and isinstance(lt, LiteralToken):
            # Value to search for with operator.
            return 2, Condition(lt, operator=op)
        case [fc, lt, *_] if isinstance(fc, Facet) and isinstance(lt, LiteralToken):
            # Value to search for in facet.
            return 2, Condition(lt, facet=fc)
        case [fc, op, lt] if (
            isinstance(fc, Facet)
            and isinstance(op, Operator)
            and isinstance(lt, LiteralToken)
        ):
            # Value to search for in facet with operator.
            return 3, Condition(lt, facet=fc, operator=op)
        case _:
            # Not matched as a condition.
            return 0, None


def parse_expression(tokens: list[Token]) -> Condition:
    """Parse an expression into a single Condition function.

    Arguments
    ---------
    tokens: list[Token]
        List of tokens to parse.

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

    conditions: list[Condition | Combiner] = []
    index = 0
    while index < len(tokens):
        # Accounts for AND/OR/NOT.
        if isinstance(combiner := tokens[index], Combiner):
            conditions.append(combiner)
            index += 1
            continue

        # Accounts for parentheses.
        offset, condition = parse_grouped_expression(tokens[index:])
        if offset > 0:
            assert condition is not None, "Only an offset of 0 returns None."
            conditions.append(condition)
            index += offset
            continue

        # Accounts for Facets, Operators, and Literals.
        offset, condition = parse_condition(tokens[index:])
        if offset > 0:
            assert condition is not None, "Only an offset of 0 returns None."
            conditions.append(condition)
            index += offset
            continue

        raise ValueError(f"Unexpected token in expression: {tokens[index]}")

    return collapse_conditions(conditions)


def collapse_nots(
    conditions: list[Condition | Combiner],
) -> list[Condition | Literal[Combiner.AND] | Literal[Combiner.OR]]:
    """Collapse all NOTs in the list of conditions.

    Parameters
    ----------
    conditions: list[Condition | Combiner]
        List of conditions and combiners.

    Returns
    -------
    collapsed_conditions: list[Condition | Combiner.AND | Combiner.OR]
        List of collapsed conditions. All NOTs have been removed.

    Raises
    ------
    ValueError
        If any NOTs are unable to be processed due to an invalid expression.
    """
    collapsed = []
    index = 0
    while index < len(conditions):
        match conditions[index : index + 2]:
            case [Combiner.NOT, Combiner.NOT]:
                # Skip double NOTs, as they negate each other.
                index += 2
            case [Combiner.NOT, right] if isinstance(right, Condition):
                collapsed.append(~right)
                index += 2
            case [left, *_] if left != Combiner.NOT:
                collapsed.append(left)
                index += 1
            case _:
                raise ValueError("Unprocessable NOT.")
    assert Combiner.NOT not in collapsed
    return collapsed


def collapse_ands(
    conditions: list[Condition | Literal[Combiner.AND] | Literal[Combiner.OR]],
) -> list[Condition | Literal[Combiner.OR]]:
    """Collapse all ANDs in the list of conditions.

    Parameters
    ----------
    conditions: list[Condition | Combiner.AND | Combiner.OR]
        List of conditions and combiners.

    Returns
    -------
    collapsed_conditions: list[Condition | Combiner.OR]
        List of collapsed conditions. All ANDs have been removed.

    Raises
    ------
    ValueError
        If any ANDs are unable to be processed due to an invalid expression.
    """
    collapsed: list[Condition | Literal[Combiner.OR]] = []
    index = 0
    while index < len(conditions):
        left = collapsed.pop() if collapsed else None
        match conditions[index : index + 2]:
            case [Combiner.AND, right] if isinstance(left, Condition) and isinstance(
                right, Condition
            ):
                collapsed.append(left & right)
                index += 2
            case [right, *_] if isinstance(left, Condition) and isinstance(
                right, Condition
            ):
                collapsed.append(left & right)
                index += 1
            case [right, *_] if right != Combiner.AND:
                if left is not None:
                    collapsed.append(left)
                collapsed.append(right)
                index += 1
            case _:
                raise ValueError("Unprocessable AND.")
    assert Combiner.AND not in collapsed
    return collapsed


def collapse_ors(
    conditions: list[Condition | Literal[Combiner.OR]],
) -> list[Condition]:
    """Collapse all ORs in the list of conditions.

    Parameters
    ----------
    conditions: list[Condition | Literal[TT.OR]]
        List of conditions and combiners.

    Returns
    -------
    collapsed_condition: List[Condition]
        A single element list containing the final condition. All ORs have been
        removed, so only a single condition should remains.

    Raises
    ------
    ValueError
        If any ORs are unable to be processed due to an invalid expression.
    """
    collapsed = []
    index = 0
    while index < len(conditions):
        match conditions[index : index + 3]:
            case [left, Combiner.OR, right] if isinstance(
                left, Condition
            ) and isinstance(right, Condition):
                collapsed.append(left | right)
                index += 3
            case [left, *_] if left != Combiner.OR:
                collapsed.append(left)
                index += 1
            case _:
                raise ValueError("Unprocessable OR.")
    assert len(collapsed) == 1 and Combiner.OR not in conditions
    return collapsed


def collapse_conditions(conditions: list[Condition | Combiner]) -> Condition:
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
    if not conditions:
        raise ValueError("No conditions to collapse.")

    # Evaluate NOTs first, left to right.
    collapsed = collapse_nots(conditions)

    # Evaluate ANDs second, left to right.
    collapsed = collapse_ands(collapsed)

    # Evaluate ORs third, left to right.
    collapsed = collapse_ors(collapsed)

    # Verify we only have a single condition at this point.
    if len(collapsed) != 1 or not isinstance(collapsed[0], Condition):
        raise ValueError("Collapse should produce a single condition.")

    return collapsed[0]


if __name__ == "__main__":
    # query = "((histogram AND field : temperature) OR (time_series AND field:humidity)) date:>= 2025-09-25T15:22Z ((!foo))"
    query = "NOT NOT NOT NOT NOT foo"
    # query = "temperature NOT(!foo)"
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
