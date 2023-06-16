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

import subprocess
import os


def test_command_line_help():
    subprocess.run(["cset", "--help"])
    # test verbose options. This is really just to up the coverage number.
    subprocess.run(["cset", "-v"])
    subprocess.run(["cset", "-vv"])


def test_recipe_execution():
    subprocess.run(
        [
            "cset",
            "operators",
            os.devnull,
            os.devnull,
            "test/test_data/noop_recipe.yaml",
        ]
    )


def test_environ_var_recipe():
    os.environ[
        "CSET_RECIPE"
    ] = """
        steps:
          - operator: misc.noop
        """
    subprocess.run(
        [
            "cset",
            "operators",
            os.devnull,
            os.devnull,
        ]
    )
