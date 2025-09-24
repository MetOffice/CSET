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

import pytest

import CSET.extract_workflow as extract_workflow


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
    # Scripts are made executable.
    assert (wd / "install_restricted_files.sh").stat().st_mode & stat.S_IXUSR
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
