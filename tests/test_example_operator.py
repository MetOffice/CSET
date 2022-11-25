import CSET.operators.example as example


def test_increment_operator():
    """Increment operator increments."""
    assert example.example_increment_operator(3) == 4
    assert example.example_increment_operator(0) == 1
    assert example.example_increment_operator(-2) == -1
    assert example.example_increment_operator(-0.5) == 0.5


def test_decrement_operator():
    """Decrement operator decrements."""
    assert example.example_decrement_operator(3) == 2
    assert example.example_decrement_operator(0) == -1
    assert example.example_decrement_operator(-2) == -3
    assert example.example_decrement_operator(-0.5) == -1.5
