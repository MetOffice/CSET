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

"""Recipe tests."""

import logging
from pathlib import Path
from textwrap import dedent

import pytest

from CSET import recipes
from CSET._common import sstrip


def test_recipe_files_in_tree():
    """Get recipes in directory containing sub-directories."""
    files = recipes._recipe_files_in_tree(input_dir=Path("tests"))
    assert Path("tests/test_data/noop_recipe.yaml") in files


def test_recipe_files_in_tree_from_package():
    """Get a recipe from inside the CSET package."""
    files = recipes._recipe_files_in_tree()
    assert any("CAPE_ratio_plot.yaml" == path.name for path in files)


def test_unpack_recipes(tmp_path: Path, caplog):
    """Unpack a recipe and check a log message is produced when files collide."""
    recipes.unpack_recipe(tmp_path, "CAPE_ratio_plot.yaml")
    assert (tmp_path / "CAPE_ratio_plot.yaml").is_file()
    with caplog.at_level("DEBUG"):
        recipes.unpack_recipe(tmp_path, "CAPE_ratio_plot.yaml")
    # Filter out unrelated log messages in case we are testing in parallel.
    _, level, message = next(
        filter(lambda r: "already exists" in r[2], caplog.record_tuples)
    )
    assert level == logging.DEBUG
    assert (
        message == "CAPE_ratio_plot.yaml already exists in target directory, skipping."
    )


def test_unpack_recipes_exception_collision(tmp_path: Path):
    """Output path already exists and is not a directory."""
    file_path = tmp_path / "regular_file"
    file_path.touch()
    with pytest.raises(FileExistsError):
        recipes.unpack_recipe(file_path, "CAPE_ratio_plot.yaml")


def test_unpack_recipes_exception_permission():
    """Insufficient permission to create output directory.

    Will fail if tests are run as root, but no one should do that, right?
    """
    with pytest.raises(OSError):
        recipes.unpack_recipe(Path("/usr/bin/cset"), "extract_instant_air_temp.yaml")


def test_get_recipe_file():
    """Get a recipe file from a specific location."""
    file = recipes._get_recipe_file("noop_recipe.yaml", Path("tests/test_data"))
    assert file.is_file()


def test_get_recipe_file_missing():
    """Exception raised when recipe file not in location."""
    with pytest.raises(FileNotFoundError):
        recipes._get_recipe_file("non-existent", Path("tests/test_data"))


def test_get_recipe_file_in_package():
    """Get a recipe file from the default location inside the package."""
    file = recipes._get_recipe_file(
        next(recipes._recipe_files_in_tree("CAPE_ratio_plot.yaml"))
    )
    assert file.is_file()


def test_list_available_recipes(capsys):
    """Display available recipes."""
    recipes.list_available_recipes()
    # Read stdout and stderr.
    captured_output = capsys.readouterr()
    # Check start.
    assert captured_output.out.startswith("Available recipes:\n")
    # Check has some recipes.
    assert len(captured_output.out.splitlines()) > 3


def test_detail_recipe(capsys):
    """Show detail of a recipe."""
    recipes.detail_recipe("CAPE_ratio_plot.yaml")
    # Read stdout and stderr.
    captured_output = capsys.readouterr()
    assert captured_output.out.startswith("\n\tCAPE_ratio_plot.yaml\n")


def test_RawRecipe_creation():
    """RawRecipe object is created properly."""
    r = recipes.RawRecipe(
        recipe="foo.yaml",
        model_ids=[1, 2, 3],
        variables={"INPUT_PATHS": ["/dev/null"]},
        aggregation=False,
    )
    assert isinstance(r, recipes.RawRecipe)
    assert r.recipe == "foo.yaml"
    assert r.model_ids == [1, 2, 3]
    assert r.variables == {"INPUT_PATHS": ["/dev/null"]}
    assert r.aggregation is False

    # Integer model_id is put into a list.
    r = recipes.RawRecipe(
        recipe="foo.yaml",
        model_ids=1,
        variables={"INPUT_PATHS": ["/dev/null"]},
        aggregation=True,
    )
    assert isinstance(r, recipes.RawRecipe)
    assert r.recipe == "foo.yaml"
    assert r.model_ids == [1]
    assert r.variables == {"INPUT_PATHS": ["/dev/null"]}
    assert r.aggregation is True


def test_RawRecipe_stringify_standard():
    """Simple case with a single model_id, and not aggregation."""
    r = recipes.RawRecipe(
        recipe="recipe.yaml",
        model_ids=1,
        variables={"INPUT_PATHS": "/dev/null"},
        aggregation=False,
    )
    expected = sstrip("""
    recipe.yaml (model 1)
    \tINPUT_PATHS /dev/null
    """)
    assert str(r) == expected


def test_RawRecipe_stringify_complex():
    """More complex case to test the indentation consistency."""
    r = recipes.RawRecipe(
        recipe="recipe.yaml",
        model_ids=[1, 2, 3],
        variables={"INPUT_PATHS": "/dev/null", "VAR": "value"},
        aggregation=True,
    )
    expected = sstrip("""
    recipe.yaml (models 1 2 3, Aggregation)
    \tINPUT_PATHS /dev/null
    \tVAR         value
    """)
    assert str(r) == expected


def test_RawRecipe_stringify_minimal():
    """Absolutely minimal case."""
    r = recipes.RawRecipe(recipe="", model_ids=1, variables={}, aggregation=False)
    expected = "<unknown> (model 1)"
    assert str(r) == expected


def test_RawRecipe_eq():
    """RawRecipe objects can be tested for equality."""
    r1 = recipes.RawRecipe(recipe="", model_ids=1, variables={}, aggregation=False)
    r2 = recipes.RawRecipe(recipe="", model_ids=1, variables={}, aggregation=False)
    r3 = recipes.RawRecipe(recipe="", model_ids=1, variables={}, aggregation=True)
    assert r1 == r1
    assert r1 == r2
    assert r1 != r3
    # NotImplemented returned for non-matching types, allowing int __eq__ to
    # take over and return False.
    assert r1 != 1


def test_RawRecipe_parbake(tmp_working_dir):
    """RawRecipe is parbaked correctly."""
    # Setup.
    recipe_file = tmp_working_dir / "recipe.yaml"
    rose_datac = tmp_working_dir / "cycle/20000101T0000Z"
    r = recipes.RawRecipe(
        recipe=str(recipe_file),
        model_ids=1,
        variables={"VAR": "value"},
        aggregation=False,
    )
    recipe_file.write_text(
        dedent(
            """\
            title: Recipe $VAR
            steps:
            - operator: misc.noop
              paths: $INPUT_PATHS
            """
        )
    )
    # Expected.
    parbaked_recipe_file = rose_datac / "recipes/recipe_value.yaml"
    expected = dedent(
        f"""\
        title: Recipe value
        steps:
        - operator: misc.noop
          paths:
          - {rose_datac / "data/1"}
        """
    )
    # Act.
    r.parbake(rose_datac, tmp_working_dir)
    # Assert.
    assert parbaked_recipe_file.exists()
    assert parbaked_recipe_file.read_text() == expected


def test_RawRecipe_parbake_aggregation(tmp_working_dir):
    """Aggregation RawRecipe is parbaked correctly."""
    # Setup.
    recipe_file = tmp_working_dir / "recipe.yaml"
    rose_datac = tmp_working_dir / "cycle/20000101T0000Z"
    r = recipes.RawRecipe(
        recipe=str(recipe_file),
        model_ids=[1, 2, 3],
        variables={"VAR": "value"},
        aggregation=True,
    )
    recipe_file.write_text(
        dedent(
            """\
            title: Recipe $VAR
            steps:
            - operator: misc.noop
              paths: $INPUT_PATHS
            """
        )
    )
    # Expected.
    parbaked_recipe_file = rose_datac / "aggregation_recipes/recipe_value.yaml"
    expected = dedent(
        f"""\
        title: Recipe value
        steps:
        - operator: misc.noop
          paths:
          - {tmp_working_dir / "cycle/*/data/1"}
          - {tmp_working_dir / "cycle/*/data/2"}
          - {tmp_working_dir / "cycle/*/data/3"}
        """
    )
    # Act.
    r.parbake(rose_datac, tmp_working_dir)
    # Assert.
    assert parbaked_recipe_file.exists()
    assert parbaked_recipe_file.read_text() == expected


def test_Config():
    """Config allows accessing variables as attributes and defaults to []."""
    conf = recipes.Config({"VARIABLE": "value"})
    assert conf.VARIABLE == "value"
    assert conf.UNDEFINED == []


def test_Config_asdict():
    """Config can return a dictionary."""
    d = {"VARIABLE": "value"}
    conf = recipes.Config(d)
    assert conf.asdict() == d


def test_load_recipes_no_variables():
    """All loaders return no recipes when variables are undefined."""
    loaded_recipes = list(recipes.load_recipes({}))
    assert len(loaded_recipes) == 0


def test_load_recipes():
    """Check that we can load recipes from a loader."""
    loaded_recipes = list(recipes.load_recipes({"TESTING_RECIPE": True}))
    expected = [
        recipes.RawRecipe("test.yaml", 1, {}, aggregation=False),
        recipes.RawRecipe("test-agg.yaml", 1, {}, aggregation=True),
    ]
    assert loaded_recipes == expected
