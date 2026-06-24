# © Crown copyright, Met Office (2022-2026) and CSET contributors.
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

"""Workflow validation tests."""

import subprocess

import pytest


@pytest.mark.cylc
def test_minimal_workflow_validation(workflow):
    """Check a minimal workflow validates.

    This essentially checks that the cylc workflow has correct syntax and that
    the example rose-suite.conf is sufficiently populated.
    """
    # Validate using the test_validate optional config.
    cmd = ("cylc", "validate", str(workflow), "--opt-conf-key", "test_validate")
    subprocess.run(cmd, check=True)


@pytest.mark.cylc
def test_rose_metadata(workflow):
    """Check that the rose metadata is well-formed."""
    cmd = ("rose", "metadata-check", "--config", str(workflow / "meta"))
    subprocess.run(cmd, check=True)


@pytest.mark.cylc
def test_rose_macro_validation(workflow):
    """Check the rose configuration matches its metadata."""
    # Populate SITE setting.
    with open(workflow / "rose-suite.conf", "rt") as fp:
        conf = fp.read().replace("SITE=", 'SITE="localhost"')
    with open(workflow / "rose-suite.conf", "wt") as fp:
        fp.write(conf)
    # Validate the configuration against the metadata.
    cmd = ("rose", "macro", "--validate", "--config", str(workflow))
    subprocess.run(cmd, check=True)
