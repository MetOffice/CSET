Glossary
========

This page describes specific terminology and concepts used within CSET.

.. glossary::
    :sorted:

    Operator
        The smallest CSET unit. E.g. read data, write data, filter data,
        stratify data.

    METplus Wrapper
        The smallest METplus unit.

    Recipe
        Consists of a combination of CSET Operators that gives i.e. temperature
        bias. This can be written and plotted or processed further. Defined in a
        YAML file.

    Diagnostic
        Stepping through a series of CSET Recipes and METplus Wrappers resulting
        in a data file that is plotted. Each diagnostic is a final output.
