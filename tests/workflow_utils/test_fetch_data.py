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

"""Tests for fetch_data workflow utility."""

from CSET._workflow_utils import fetch_data_filesystem, validity_time_tester


def test_function_exists():
    """Placeholder tests before rewriting fetch data utility."""
    # TODO: Write tests after switching to new fetch_data utility.
    assert callable(fetch_data_filesystem.run)
    assert callable(validity_time_tester.create_validity_time_tester)
