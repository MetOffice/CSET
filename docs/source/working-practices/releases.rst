Release Management
==================

This will be some way off for now, but it is useful to have a policy/documented
process for making a release. Making stable releases is important as it gives
everyone something to rally around, whether  developers wanting to get in a
certain feature, or users wanting to find out what has changed.

Scientists like having stable versions to be able to finish their paper with, or
otherwise do their work without things changing.

For making a release a branch is created with push protection that is
effectively frozen. The relevant commit is also tagged with the release number.
Ideally releases should be mostly automated, as that helps prevent accidents
(like publishing a broken build) happening.

Part of this will be considering our versioning strategy. I'm leaning towards
`CalVer <https://calver.org/>`_.
