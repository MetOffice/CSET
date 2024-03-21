Run an Operator Recipe
======================

Operators individually don't form a complete task. Instead they need to be
chained together with *operator recipes*. A recipe is a config file that details
what operators to run, in what order, and with what extra arguments. Each recipe
forms a complete chain processing an input file and producing an output file.

Operator recipes can be run either with the :ref:`cset-bake-command` command, or
from a python script.

.. code-block:: python

    from pathlib import Path
    import CSET.operators

    CSET.operators.execute_recipe(
        Path("/path/to/recipe_file.yaml"),
        Path("/path/to/input_file.nc"),
        Path("/path/to/output_file.nc")
    )

The format of recipe files is described in :doc:`/reference/recipe-format`.

There are number of included recipe files you can use before having to create
your own. These can be retrieved with the :ref:`cset-cookbook-command` command.
