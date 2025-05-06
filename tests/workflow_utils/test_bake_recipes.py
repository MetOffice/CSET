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

"""Tests for bake_recipes workflow utility."""

import os
import subprocess

import pytest

from CSET._workflow_utils import bake_recipes


def test_get_configuration(monkeypatch, tmp_path):
    """Basic configuration correctly extracted from environment variables."""
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", str(tmp_path))
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", "20000101T0000Z")

    recipe_dir = tmp_path / "cycle/20000101T0000Z/recipes"
    recipe_dir.mkdir(parents=True)
    for n in range(3):
        (recipe_dir / f"r{n}.yaml").touch()

    cset_args, plot_dir, recipe_files, nproc = bake_recipes.get_configuration()
    assert cset_args == []
    assert plot_dir == f"{tmp_path}/web/plots/20000101T0000Z"
    assert sorted(recipe_files) == [str(recipe_dir / f"r{n}.yaml") for n in range(3)]
    assert nproc == len(os.sched_getaffinity(0))


def test_get_configuration_case_aggregation(monkeypatch, tmp_path):
    """Case aggregation configuration correctly extracted."""
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", str(tmp_path))
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", "20000101T0000Z")
    monkeypatch.setenv("DO_CASE_AGGREGATION", "True")

    recipe_dir = tmp_path / "cycle/20000101T0000Z/aggregation_recipes"
    recipe_dir.mkdir(parents=True)
    for n in range(3):
        (recipe_dir / f"r{n}.yaml").touch()

    cset_args, plot_dir, recipe_files, nproc = bake_recipes.get_configuration()
    assert cset_args == []
    assert plot_dir == f"{tmp_path}/web/plots/20000101T0000Z"
    assert sorted(recipe_files) == [str(recipe_dir / f"r{n}.yaml") for n in range(3)]
    assert nproc == 1


def test_get_configuration_CLI_args(monkeypatch):
    """Command line argument configuration correctly extracted."""
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", "/share")
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", "20000101T0000Z")
    monkeypatch.setenv("COLORBAR_FILE", "/share/style.json")
    monkeypatch.setenv("PLOT_RESOLUTION", "100")
    monkeypatch.setenv("SKIP_WRITE", "True")

    cset_args, plot_dir, recipe_files, nproc = bake_recipes.get_configuration()
    assert cset_args == [
        "--style-file='/share/style.json'",
        "--plot-resolution=100",
        "--skip-write",
    ]
    assert plot_dir == "/share/web/plots/20000101T0000Z"
    assert recipe_files == []
    assert nproc == len(os.sched_getaffinity(0))


def test_bake_recipe(monkeypatch):
    """A single recipe is baked correctly."""
    function_ran = False

    def mock_subprocess_run(command, check):
        nonlocal function_ran
        function_ran = True
        assert check
        assert command == [
            "cset",
            "bake",
            "--recipe",
            "/recipes/recipe.yaml",
            "--output-dir",
            "/plots/recipe",
            "--custom-argument",
        ]

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    recipe_name = bake_recipes.bake_recipe(
        "/recipes/recipe.yaml", ["--custom-argument"], "/plots"
    )
    assert recipe_name == "recipe"


def test_bake_recipe_subprocess_error(monkeypatch, capsys):
    """A single recipe is baked correctly."""

    def mock_subprocess_run(command, check):
        raise subprocess.CalledProcessError(42, command)

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    with pytest.raises(subprocess.CalledProcessError):
        bake_recipes.bake_recipe("/recipes/recipe.yaml", [], "/plots")
    assert (
        capsys.readouterr().out
        == "Baking of /recipes/recipe.yaml failed. Exited with code 42\n"
    )


def test_bake_all(monkeypatch):
    """Baking jobs are correctly submitted and collected for all recipes."""
    recipes = ["r1.yaml", "r2.yaml", "r3.yaml"]
    run_recipes = []

    def mock_get_configuration():
        # cset_args, plot_dir, recipe_files, nproc
        return [], "", recipes, 1

    def mock_bake_recipe(recipe_file, cset_args, plot_dir):
        nonlocal run_recipes
        run_recipes.append(recipe_file)
        return "recipe"

    monkeypatch.setattr(bake_recipes, "get_configuration", mock_get_configuration)
    monkeypatch.setattr(bake_recipes, "bake_recipe", mock_bake_recipe)

    bake_recipes.bake_all()
    assert run_recipes == recipes


def test_bake_all_no_recipes(monkeypatch):
    """Exits non-zero when there are no recipes to process."""

    def mock_get_configuration():
        # cset_args, plot_dir, recipe_files, nproc
        return [], "", [], 1

    def mock_bake_recipe(recipe_file, cset_args, plot_dir):
        return "recipe"

    monkeypatch.setattr(bake_recipes, "get_configuration", mock_get_configuration)
    monkeypatch.setattr(bake_recipes, "bake_recipe", mock_bake_recipe)

    with pytest.raises(SystemExit) as exc_info:
        bake_recipes.bake_all()
        assert exc_info.value.code == 1


def test_entrypoint(monkeypatch):
    """Check that bake_recipes.run() calls the correct function."""
    function_ran = False

    def assert_true():
        nonlocal function_ran
        function_ran = True

    monkeypatch.setattr(bake_recipes, "bake_all", assert_true)
    bake_recipes.run()
    assert function_ran, "Function did not run!"


def test_entrypoint_exit_on_subprocess_exception(monkeypatch):
    """Check that bake_recipes.run() exits non-zero."""

    def subprocess_error():
        raise subprocess.CalledProcessError(1, "foo")

    monkeypatch.setattr(bake_recipes, "bake_all", subprocess_error)
    with pytest.raises(SystemExit) as exc_info:
        bake_recipes.run()
        assert exc_info.value.code == 1
