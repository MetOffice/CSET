Using Recipe Variables
======================

A CSET recipe may contain variables. These are values filled in at runtime, and
allow making generic recipes that can handle multiple cases. This prevents the
need to have hundreds of recipes for every combination.

A variable can be added to a recipe by setting a parameter's value to the
variable name, prefixed with a dollar sign. This name may only contain upper
case letters and underscores. For example:

.. code-block:: yaml

    parameter: $MY_VARIABLE

When the recipe is run with ``cset bake`` the variable is replaced with a value
given on the command line. This is done using the variable name as an option,
for example:

.. code-block:: bash

    cset bake -i input -o output -r recipe.yaml --MY_VARIABLE='value'

The given value will be templated into the parameter so what runs is actually:

.. code-block:: yaml

    parameter: value
