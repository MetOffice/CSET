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

"""Load testing recipes."""

from CSET.recipes import Config, RawRecipe


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    if conf.TESTING_RECIPE:
        # test.yaml recipe doesn't actually exist.
        yield RawRecipe("test.yaml", 1, {}, aggregation=False)
        yield RawRecipe("test-agg.yaml", 1, {}, aggregation=True)
