# NCI CSET Demo

Runs a sample CSET configuration at NCI. This can be used for testing new CSET releases or pull requests or as a general demo.

Run the demo by checking out a copy of CSET (if you're testing a specific branch check out that branch) e.g.:

    git clone -b 2539-nci-demo-configuration https://github.com/metoffice/cset

then from within the checked-out repo run

    ./utils/nci-demo/nci-demo.sh

This will install the CSET workflow and run it using the ['nci-demo'](/src/CSET/cset_workflow/opt/rose-suite-nci-demo.conf) opt file.
The opt file configures CSET to run against sample data held in /g/data/dp9.
The version of CSET in the workflow will be from the checked out repository, rather than the module, so it will make use of any new features.

The Cylc run will be named `cset-demo/$BRANCH_NAME`.
If the run already exists it will be updated from the checked out repository, to start a new run clear out the old one with `cylc clean`.
