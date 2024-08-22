# © Crown copyright, Met Office (2022-2024) and CSET contributors.
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

"""Tests for finish_website workflow utility."""

from CSET._workflow_utils import finish_website


def test_write_workflow_status(monkeypatch, tmp_path):
    """Workflow  finish status gets written to status file."""
    monkeypatch.setenv("WEB_DIR", str(tmp_path))
    finish_website.run()
    with open(tmp_path / "status.html") as fp:
        assert fp.read() == "<p>Finished</p>\n"
