# © Crown copyright, Met Office (2022-2025) and CSET contributors.
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

"""Tests for install workflow utility."""

import os
import stat
import subprocess
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from CSET import extract_workflow


@pytest.fixture(scope="session")
def restricted_git_repo() -> Generator[str]:
    """Return the path to a local git repository."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_location = Path(tmp_dir) / "restricted-git-repo"
        repo = str(repo_location.absolute())

        # Create some content.
        repo_location.mkdir()
        (repo_location / "README.md").write_text("# Test restricted repository\n")
        (repo_location / ".hidden").write_text("hidden file\n")
        (repo_location / "restricted_file.txt").write_text("restricted data\n")

        # Git commands for creating a minimal repository of the right structure.
        commands = [
            ("git", "init", "-b", "main", repo),
            ("git", "-C", repo, "add", "."),
            ("git", "-C", repo, "commit", "-m", "Add stuff"),
            ("git", "-C", repo, "branch", "releases/v1.0"),
            ("git", "-C", repo, "tag", "-am", "Version 1.0", "v1.0.0", "releases/v1.0"),
        ]
        # Explicitly set author/committer identities in case they are not
        # configured, such as on GitHub Actions runners.
        env = os.environ.copy()
        env["GIT_AUTHOR_NAME"] = "name"
        env["GIT_AUTHOR_EMAIL"] = "name@example.com"
        env["GIT_COMMITTER_NAME"] = "name"
        env["GIT_COMMITTER_EMAIL"] = "name@example.com"
        for command in commands:
            subprocess.run(command, check=True, env=env)

        # Yield path to repo. This will be cleaned up after the tests finish.
        yield repo


def test_make_script_executable_script(tmp_path):
    """Script files are made executable."""
    f = tmp_path / "file"
    # Mode is u=rw,g=r,o=r
    f.touch(mode=stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    f.write_text("#!/usr/bin/env bash\necho 'Hello world!'")
    extract_workflow.make_script_executable(f)
    # Check that everyone who had read permission now can execute.
    mode = f.stat().st_mode
    assert (mode & stat.S_IXUSR) and (mode & stat.S_IXGRP) and (mode & stat.S_IXOTH)

    # Mode is u=rw,g=r
    f.chmod(mode=stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
    extract_workflow.make_script_executable(f)
    # Check that other cannot now execute.
    mode = f.stat().st_mode
    assert (mode & stat.S_IXUSR) and (mode & stat.S_IXGRP) and not (mode & stat.S_IXOTH)

    # Mode is u=rw
    f.chmod(mode=stat.S_IRUSR | stat.S_IWUSR)
    extract_workflow.make_script_executable(f)
    # Check that group and other cannot now execute.
    mode = f.stat().st_mode
    assert (
        (mode & stat.S_IXUSR)
        and not (mode & stat.S_IXGRP)
        and not (mode & stat.S_IXOTH)
    )

    # Mode is unreadable.
    f.chmod(mode=0)
    extract_workflow.make_script_executable(f)
    # Check that no one can execute.
    mode = f.stat().st_mode
    assert (
        not (mode & stat.S_IXUSR)
        and not (mode & stat.S_IXGRP)
        and not (mode & stat.S_IXOTH)
    )


def test_make_script_executable_not_script(tmp_path):
    """Non-script files are not made executable."""
    f = tmp_path / "file"
    # Mode is u=rw,g=r,o=r
    f.touch(mode=stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    f.write_text("Not a script file.")
    extract_workflow.make_script_executable(f)
    # Check that no one can execute.
    mode = f.stat().st_mode
    assert (
        not (mode & stat.S_IXUSR)
        and not (mode & stat.S_IXGRP)
        and not (mode & stat.S_IXOTH)
    )


def test_make_script_executable_not_file(tmp_path):
    """Non-files are not made executable."""
    d = tmp_path / "dir"
    d.mkdir(mode=0o500)
    extract_workflow.make_script_executable(d)
    assert d.is_dir()
    # Check mode is unchanged.
    mode = d.stat().st_mode
    assert (
        (mode & stat.S_IRUSR)
        and (mode & stat.S_IXUSR)
        and not (mode & stat.S_IRGRP)
        and not (mode & stat.S_IXGRP)
        and not (mode & stat.S_IROTH)
        and not (mode & stat.S_IXOTH)
    )


def test_make_script_executable_short_file(tmp_path):
    """Short files (<14 bytes) are not marked executable."""
    f = tmp_path / "file"
    # Mode is u=rw,g=r,o=r
    f.touch(mode=stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    extract_workflow.make_script_executable(f)
    mode = f.stat().st_mode
    assert (
        not (mode & stat.S_IXUSR)
        and not (mode & stat.S_IXGRP)
        and not (mode & stat.S_IXOTH)
    )


def test_install_workflow(monkeypatch, tmp_path):
    """Test workflow is installed correctly."""
    conda_env = tmp_path / "conda-env"
    conda_env.mkdir()
    monkeypatch.setenv("CONDA_PREFIX", str(conda_env))
    extract_workflow.install_workflow(tmp_path)
    # Check workflow directory has been created.
    subdirs = list(tmp_path.glob("cset-workflow-v*/"))
    assert len(subdirs) == 1
    wd = subdirs[0]
    assert wd.name.startswith("cset-workflow-v")
    assert wd.is_dir()
    # Regular files are coped.
    assert (wd / "flow.cylc").is_file()
    # Conda environment is linked.
    assert (wd / "conda-environment").is_symlink()
    assert (wd / "conda-environment").readlink() == conda_env


def test_install_workflow_no_conda_prefix(monkeypatch, tmp_path):
    """Workflow is installed without conda environment symlink."""
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    extract_workflow.install_workflow(tmp_path)
    wd = next(tmp_path.glob("cset-workflow-v*/"))
    assert not os.path.lexists(wd / "conda-environment")


def test_install_workflow_not_dir(tmp_path):
    """Exception raised when location is not a directory."""
    file = tmp_path / "file"
    file.touch()
    with pytest.raises(OSError, match=f"{file} should exist and be a directory."):
        extract_workflow.install_workflow(file)


def test_install_workflow_dir_already_exists(tmp_path):
    """Exception raised when there is already a workflow dir at location."""
    # Run once to create initial version.
    extract_workflow.install_workflow(tmp_path)
    # Run again to cause error.
    with pytest.raises(
        FileExistsError, match=f"Refusing to overwrite {tmp_path}/cset-workflow-v"
    ):
        extract_workflow.install_workflow(tmp_path)


def test_list_refs(restricted_git_repo: str):
    """Test listing release references."""
    refs = extract_workflow.list_refs(restricted_git_repo)
    assert isinstance(refs, list)
    assert len(refs) == 2
    assert set(refs) == {"releases/v1.0", "v1.0.0"}


def test_list_refs_no_repo_access():
    """Exception raised when listed repository does not exist."""
    with pytest.raises(ValueError, match="Cannot access Git repository"):
        extract_workflow.list_refs("/non-existent/git/repo")


def test_clone_ref(tmp_path: Path, restricted_git_repo: str):
    """Clone a ref from a repository."""
    ref = "v1.0.0"
    url = restricted_git_repo
    location = str(tmp_path)
    extract_workflow.clone_ref(ref, url, location)
    assert (tmp_path / "README.md").exists()
    assert (tmp_path / "restricted_file.txt").exists()


def test_clone_ref_no_repo_access(tmp_path: Path):
    """Exception raised when cloned repository does not exist."""
    ref = "v1.0.0"
    url = "/non-existent/git/repo"
    location = str(tmp_path)
    with pytest.raises(ValueError, match="Cannot access ref .+ from Git repository at"):
        extract_workflow.clone_ref(ref, url, location)


def test_clone_ref_no_such_ref(tmp_path: Path, restricted_git_repo: str):
    """Exception raised when ref does not exist in target repository."""
    ref = "refs/tags/does-not-exist"
    url = restricted_git_repo
    location = str(tmp_path)
    with pytest.raises(ValueError, match="Cannot access ref .+ from Git repository at"):
        extract_workflow.clone_ref(ref, url, location)


def test_install_restricted_files(tmp_path: Path, restricted_git_repo: str):
    """Install restricted files from a Git repository."""
    # Make into cylc workflow.
    (tmp_path / "flow.cylc").touch()

    # Install restricted files.
    extract_workflow.install_restricted_files(tmp_path, restricted_git_repo)

    # README.md not copied.
    assert not (tmp_path / "README.md").exists()
    # Hidden files not copied.
    assert not (tmp_path / ".hidden").exists()
    # Other files are copied.
    assert (tmp_path / "restricted_file.txt").exists()
    # Existing files are untouched.
    assert (tmp_path / "flow.cylc").exists()


def test_install_restricted_files_not_workflow(tmp_path: Path):
    """Exception raised when target location is not a cylc workflow."""
    with pytest.raises(ValueError, match="should be a CSET workflow directory"):
        extract_workflow.install_restricted_files(tmp_path)


def test_install_restricted_files_no_repo_access(tmp_path: Path):
    """Exception raised when repositories cannot be accessed."""
    # Make into cylc workflow.
    (tmp_path / "flow.cylc").touch()
    with pytest.raises(ValueError, match="Could not read from restricted repository"):
        extract_workflow.install_restricted_files(tmp_path, alternative_url="/dev/null")
