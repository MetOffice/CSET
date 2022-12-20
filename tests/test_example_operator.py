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

import CSET.operators.example as example


def test_increment_operator():
    """Increment operator increments."""
    assert example.example_increment_operator(3) == 4
    assert example.example_increment_operator(0) == 1
    assert example.example_increment_operator(-2) == -1
    assert example.example_increment_operator(-0.5) == 0.5


def test_decrement_operator():
    """Decrement operator decrements."""
    assert example.example_decrement_operator(3) == 2
    assert example.example_decrement_operator(0) == -1
    assert example.example_decrement_operator(-2) == -3
    assert example.example_decrement_operator(-0.5) == -1.5
