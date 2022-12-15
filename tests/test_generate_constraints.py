from CSET.operators import generate_constraints


def test_generate_constraints_operator():
    """generate iris cube constraint for UM STASH code."""
    stash_constraint = generate_constraints.generate_stash_constraints("m01s03i236")
    assert type(stash_constraint) ==  "<class 'iris._constraints.AttributeConstraint'>"

    """generate iris cube constraint for str variable name."""
    var_constraint = generate_constraints.generate_var_constraints("test")
    assert type(var_constraint) ==  "<class 'iris._constraints.Constraint'>"


    
