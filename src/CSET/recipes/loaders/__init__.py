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

"""
Recipe loaders.

Each loader should provide a `load` function and be imported and added to
__all__ below.
"""

from CSET.recipes.loaders import (
    spatial_difference_field,
    spatial_field,
    test,
    timeseries,
)

__all__ = [
    "spatial_difference_field",
    "spatial_field",
    "test",
    "timeseries",
]
