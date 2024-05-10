Using git and GitHub
====================

If you haven't used git before, it is worth spending some time learning it
before getting stuck into development. git is the go-to code revision control
system, and is useful whether you are working alone or with others.

A good place to start learning is this `git and GitHub tutorial`_. Once you have
done that it is worth reading about the `GitHub flow`_, which is the approximate
way you should be using GitHub, as well as this short article on writing `good
commit messages`_.

For using git locally, you can use either the CLI git program, or git
functionality built into many IDEs, such as VSCode or PyCharm. As you get
started with git on the command line, you may find this `git cheat sheet`_
helpful.

.. _git and GitHub tutorial: https://aaronosher.io/github-workshop/
.. _GitHub flow: https://docs.github.com/en/get-started/quickstart/github-flow
.. _good commit messages: https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
.. _git cheat sheet: https://education.github.com/git-cheat-sheet-education.pdf

Setting up git
--------------

If you don't yet have it, git can be installed from the `official git website`_.
On Linux it can be acquired through your package manager, though it is often
installed by default. The command ``git help`` can be used to check if it is
installed, and will give you an overview of some common commands.

Once installed, the following command will set up your identity on git, and only
needs to be done once. These details will go alongside your commits.

.. code-block:: bash

    git config --global user.name "Your Name"
    git config --global user.email "your-email@example.com"


.. _official git website: https://git-scm.com/

Authenticating git with GitHub
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you clone a private repository GitHub needs to verify you have permission
to access it. There are two ways of authentication in git: via HTTPS, or via
SSH, with SSH being recommended.

Cloning via HTTPS is good for when you are behind restrictive proxies that block
all internet traffic except websites. You will either have to setup the `Git
Credential Manager`_, which may not be installed by default, or use the `GitHub
CLI to authenticate`_, and `configure git to use it`_. In environments where you
can't install additional software, use the SSH method instead.

Cloning via SSH is good when you already have an SSH key, and it is simpler (and
arguably more secure) than cloning via HTTPS. `GitHub's documentation on SSH`_
covers setting it up. To access repositories within an enterprise environment
(such as this one) you will also have to `setup single sign-on`_.

.. _Git Credential Manager: https://github.com/GitCredentialManager/git-credential-manager/blob/main/README.md
.. _GitHub CLI to authenticate: https://cli.github.com/manual/gh_auth_login
.. _configure git to use it: https://cli.github.com/manual/gh_auth_setup-git
.. _GitHub's documentation on SSH: https://docs.github.com/en/authentication/connecting-to-github-with-ssh
.. _setup single sign-on: https://docs.github.com/en/enterprise-cloud@latest/authentication/authenticating-with-saml-single-sign-on/authorizing-an-ssh-key-for-use-with-saml-single-sign-on

Useful git commands
-------------------

While git has many commands, for most things you will find the following list of
commands sufficient. More detail on each of these commands can be found in the
`git reference documentation`_.

.. csv-table::
    :header: "Command", "Description"
    :widths: auto

    "``git status``", "Status of repository, showing changed files, etc."
    "``git clone <repo-url>``", "Download code"
    "``git add <filename>``", "Add a modified or new file to your next commit"
    "``git branch``", "List local branches"
    "``git switch <branch>``", "Switch to an existing branch"
    "``git switch -c <branch>``", "Create a new branch in your local repository"
    "``git commit``", "Commit changes to local repository"
    "``git push``", "Push changes or new branch up to the remote repository (GitHub)"
    "``git log``", "Log of previous commits in current branch"
    "``git diff``", "Show changes since last commit in local directory"
    "``git fetch``", "Fetch remote changes from GitHub, but don't apply them"
    "``git merge <src-branch>``", "Merge changes from another branch into the current one"
    "``git pull``", "Update local branch with remote changes (a combined fetch and merge)"

.. _git reference documentation: https://git-scm.com/docs

.. _pull-request:

Pull Request
------------

A pull request is how you submit code for inclusion in CSET. All code changes
must go through a pull request. Pushing directly to the main branch has been
disabled. Before being merged, code will have to go through several stages of
review.

A pull request should generally be a complete feature, and can have as many
commits as needed, as well as being able to be worked on by multiple people. A
new diagnostic chain would be a reasonable level for a pull request, but smaller
ones are also just fine as long as they are "complete". The idea is that the
main branch should always "work", and thus any incomplete or broken
functionality shouldn't be merged in.

.. note::

    Early in development (where we are with CSET as of November 2022) the main
    branch will change hugely very quickly, and CSET doesn't work at all yet,
    and thus pull requests can be much smaller with less stringent requirements
    for merging.

For large features that might taken many months to develop, the main branch may
change too much to merge in the changes cleanly. This can be countered by
rebasing, which is where git reapplies your changes on an up-to-date copy of the
main branch, letting you fix any issues that occur. If you do this regularly
then any fixes should be easy.

A large diagnostic might however be broken out into several pull requests if
there are distinct components. For example, if it needs new operators that could
potentially be used by another diagnostic, then it makes sense to have those
operators in separate pull requests so they can be merged when needed.

Review steps
~~~~~~~~~~~~

There are a number of steps that a pull request has to go through before it can
be merged into the main branch.

The first will be the automatic tests being run by the CI system. This
automatically happens when you make a pull request against the main branch, and
is a good catcher of initial problems. Generally you should resolved any test
failures before asking for code review. The page on :doc:`testing` goes into
more detail.

The next step will be getting other people to look at your code. This involves
three reviews, covering the technical, scientific, and portability aspects of
your submission. A minor change, such as fixing a typo or an obvious bug fix,
would only require sign-off from the technical reviewer, and would be a lot
quicker. More detail is on the :doc:`code-review` page.

From the review you will probably receive feedback, and things to change and
improve. Once these points have been addressed the code can be merged into the
main branch, and become part of CSET proper.

Git terminology
---------------

**Repository**: A directory that contains a .git folder and all of your code. It
contains everything related to git, and is entirely local.

**Working Tree**: The current state of the tracked files within the repository.
This is what you actually edit while coding.

**Index**: AKA the staging area. The index will become the next commit, and is
added to via the ``git add <file>`` command. To unstage changes use the
``git restore --staged <file>`` command. Having this index makes it easier
to split a change into multiple commits if desired.

**Commits**: The core unit of git. Each commit describes the state of the
working tree at the point where it is committed. Contains information like a
commit message, the date when the commit was made, and author information. It
also contains a reference to any parent commits, which defines the repository
history. Create a new commit with the ``git commit`` command. When fixing
an issue include the issue number in the commit message body, e.g.:

.. code-block:: text

    Stop foo doing bar

    Description of why this change was made.
    Fixes #123

**Branch**: A special reference to a particular commit. If a new child commit is
created the reference moves to that new commit.

* List your local branches with the command ``git branch``.
* Create a new branch with ``git switch -c <branch-name>``.
* Switch between local branches with the command ``git switch <branch-name>``. You
  will need to commit your changes before switching.


**Tag**: A special reference to a a particular commit. Unlike a branch it doesn't
move.

git rebase
~~~~~~~~~~

A rebase changes the base commit from which your changes are made. The rebase
command ordinarily takes the form ``git rebase [new-base-branch]``, which
starts a rebase. Your branch will be reset so it is the same as the new base,
and the changes you have made will be applied to it sequentially.

Git will try and do this automatically, however if a conflict occurs it needs to
be manually resolved before running ``git rebase --continue`` to finish the
rebase.

There is a good overview of rebasing in `these slides`_, and the `official
documentation on rebase`_ goes into a lot more detail.

When rebasing or merging there are times when git cannot proceed. This is called
a conflict and often occurs if you have changed a line that was also changed in
the other branch. Git will stop and let you manually fix it. Read the
`documentation on fixing merge conflicts`_ to find out how.

.. _these slides: https://aaronosher.io/github-workshop/#rebase
.. _official documentation on rebase: https://git-scm.com/book/en/v2/Git-Branching-Rebasing
.. _documentation on fixing merge conflicts: https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging#_basic_merge_conflicts
