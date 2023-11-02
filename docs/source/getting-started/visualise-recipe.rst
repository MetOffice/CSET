Visualising a recipe graphically
================================

.. Tutorial on cset graph and introduction to the recipe format.

In this tutorial we will investigate what is going on inside of a recipe, and
visualise the *operators* inside.

Using the ``cset cookbook`` command find the "Mean Air Temperature Spatial Plot"
recipe, and click the button to use it. This will write out a ``.yaml`` file to
your current directory containing your selected recipe.

We will now visualise the steps inside the recipe using the ``cset graph``
command.

.. code-block:: bash

    cset graph recipe.yaml

This should open an image of a visualisation of the recipe. Each node is a step,
or an *operator*, which does a single processing task. You can see that later
operators depend on previous ones, and this relationship can be as complicated
as needed.

.. Include image of visualised recipe.

.. Discussion of the specific operators shown.

To see more detail about each individual operator running we can use the
``--details`` flag. This shows the configuration of each operator in the recipe.

.. code-block:: bash

    cset graph --details recipe.yaml

.. Discussion of configuration of the shown operators.

You now know how to visualise a recipe, and a little about the operators it is
made up of. In the next tutorial you will learn to make your own.
