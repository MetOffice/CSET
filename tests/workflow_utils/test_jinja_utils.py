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

"""Tests for jinja_utils functions."""

import base64
import json

import CSET.cset_workflow.lib.python.jinja_utils as jinja_utils


def test_b64json_list():
    """Check a list can be encoded as base64ed JSON."""
    input_list = [1, "two", 3.0]
    expected = "WzEsICJ0d28iLCAzLjBd"
    actual = jinja_utils.b64json(input_list)
    assert actual == expected


def test_b64json_dict():
    """Check a dictionary can be encoded as base64ed JSON."""
    input_dict = {"foo": 1, "bar": {"baz": 2}}
    expected = "eyJmb28iOiAxLCAiYmFyIjogeyJiYXoiOiAyfX0="
    actual = jinja_utils.b64json(input_dict)
    assert actual == expected


def test_b64json_remove_rose_suite_variables():
    """Check reference to circular ROSE_SUITE_VARIABLES is removed."""
    input_dict = {"foo": 1, "ROSE_SUITE_VARIABLES": 2, "bar": 3}
    encoded = jinja_utils.b64json(input_dict)
    assert "ROSE_SUITE_VARIABLES" not in json.loads(base64.b64decode(encoded))


def test_get_models():
    """Check a list of model dictionaries can be built."""
    ROSE_SUITE_VARIABLES = {
        "m1_name": "foo",
        "m1_number": 1000,
        "m2_name": "bar",
        "m2_number": 2000,
    }
    models = jinja_utils.get_models(ROSE_SUITE_VARIABLES)
    expected_models = [
        {"id": 1, "name": "foo", "number": 1000},
        {"id": 2, "name": "bar", "number": 2000},
    ]
    assert isinstance(models, list)
    assert models == expected_models
