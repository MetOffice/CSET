# Copyright 2022 Met Office and contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
        stash code to build iris constrain, currently using "m01s03i236"

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


def generate_var_constraints(varname: str, **kwargs) -> iris.Constraint:
    """
    Operator that takes a CF compliant variable name string, and uses iris to generate
    a constraint to be passed into the read operator to minimize the CubeList the
    read operator loads and speed up loading.
    This is not replacing the more fine grained filter operator.
    At a later stage str list required to combine constraints.

    Arguments
    ---------
    varname: str
        CF compliant name of variable. Needed later for LFRic. Currently using "test"

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
