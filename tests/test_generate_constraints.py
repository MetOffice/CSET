from CSET.operators import generate_constraints


def test_generate_constraints_operator():
    """generate iris cube constraint for UM STASH code."""
    stash_constraint = generate_constraints.generate_stash_constraints("m01s03i236")
    #    expected_stash_constraint = "<class 'iris._constraints.AttributeConstraint'>"
    #    assert type(stash_constraint) == expected_stash_constraint
    expected_stash_constraint = "AttributeConstraint({'STASH': 'm01s03i236'})"
    assert repr(stash_constraint) == expected_stash_constraint

    """generate iris cube constraint for str variable name."""
    var_constraint = generate_constraints.generate_var_constraints("test")
    # expected_var_constraint = "<class 'iris._constraints.Constraint'>"
    # assert type(var_constraint) == expected_var_constraint
    expected_var_constraint = "Constraint(name='test')"
    assert repr(var_constraint) == expected_var_constraint
