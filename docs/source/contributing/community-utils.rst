Community Utilities
===================

Many datasets require custom processing before they can be used.
As CSET cannot support every dataset natively we instead turn to
community maintained utilities to preprocess the data into a common form
before CSET is run.

You can find community utilities within the `utils directory`_ of the CSET repository.
If you have any queries or issues with a utility,
please contact the owner named in that utility's README.

.. _utils directory: https://github.com/MetOffice/CSET/tree/main/utils

Requirements for a community utility
------------------------------------

To ensure utilities are sustainable they must meet the following requirements:

* Each utility lives in its own ``utils/<utility-name>/`` directory within the main CSET repository.
* Each utility must have a README document describing what it does and how to use it.
* Each utility must have at least one named owner, who is responsible for maintaining it.
* Utilities should document their own environment.
  The main CSET environment may remove packages without notice.
* Utilities should generally output to a user specified directory in a common data format, such as NetCDF.
* Utilities go through the normal CSET review process,
  both so they can benefit from other's insight and so they can inform CSET development for common requirements.
* Automatic testing is encouraged and will block merging of PRs that break them.
  Utilities will not be manually tested as part of CSET development; this is the responsibility of the utility's owner.

An example utility illustrating these requirements can be found in `utils/example_utility`_.

.. _utils/example_utility: https://github.com/MetOffice/CSET/tree/main/utils/example_utility
