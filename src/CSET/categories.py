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

"""Define categories and sub categories for CSET recipes."""

from enum import StrEnum


class Category(StrEnum):
    """Valid Categories for CSET recipes."""

    DIAGNOSTICS = "Diagnostics"
    VERIFICATION = "Verification"


class Subcategory(StrEnum):
    """Valid Subcategories for CSET recipes."""

    SURFACE = "Surface"
    UPPER_AIR = "Pressure Level"
    DETERMINISTIC = "Model Level"
    ENSEMBLE = "Ensembles"
    DERIVED_DIAGNOSTICS = "Derived Diagnostics"
