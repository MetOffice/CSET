"""
Operators to generate load constraints and pass into read operator.
"""

import iris
import iris.cube


def generate_stash_constraints(stash: str) -> iris.AttributeConstraint:
    
    """
    Operator that takes a stash string, and uses iris to generate a constraint to be 
    passed into the read operator to minimize the CubeList the 
    read operator loads and speed up loading.

    This is not replacing the more fine grained filter operator.
    At a later stage str list required to combine constraints.
    Arargument should be a list of stash codes that combined build 
    the constraint.

    Arguments
    ---------
    stash: str 
        stash code to build iris constrain
    
    Returns
    -------
    stash_constraint: iris.AttributeConstraint
    """
    
    # Load stash codes as type iris.Attribute as well as names as iris.Constraint
    if type(stash) == str:
        stash_constraint = iris.AttributeConstraint(STASH=stash)
        return stash_constraint
    else:
        print("Further constraint conditions required...")
        
        
def generate_var_constraints(varname: str) -> iris.Constraint:
    
    """
    Operator that takes a CF compliant variable name string, and uses iris to generate 
    a constraint to be passed into the read operator to minimize the CubeList the 
    read operator loads and speed up loading.
    This is not replacing the more fine grained filter operator.
    At a later stage str list required to combine constraints.
    
    Arguments
    ---------
    varname: str
        CF compliant name of variable. Needed later for LFRic.
    
    Returns
    -------
    varname_constraint: iris.Constraint
    """
    
    # Need to load stash codes as type iris.Attribute as well as names as iris.Constraint
    if type(varname) == str:
        varname_constraint = iris.Constraint(name=varname)
        return varname_constraint
    else:
        print("Further constraint conditions required...")
        
