import CSET.operators.example as example


def test_example_operator():
    assert example.example_operator(3) == 4
    assert example.example_operator(0) == 1
    assert example.example_operator(-2) == -1
    assert example.example_operator(-0.5) == 0.5
