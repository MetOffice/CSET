# Copyright 2022 Met Office and contributors.
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

from pathlib import Path

import pytest

import CSET.graph


def test_save_graph():
    """Directly tests generating a graph from a recipe file without the output
    specified."""
    CSET.graph.save_graph(Path("tests/test_data/plot_instant_air_temp.yaml"))

    # Test exception for recipe without an operator in a step.
    with pytest.raises(ValueError):
        CSET.graph.save_graph(
            """\
            steps:
                - argument: no_operators
            """
        )
