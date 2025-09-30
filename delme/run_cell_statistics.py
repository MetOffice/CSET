from pathlib import Path

from CSET._common import parse_recipe
from CSET.operators import execute_recipe


recipe_fpath = (
    Path(__file__).parent.parent / "src" / "CSET" / "recipes" / "cell_statistics.yaml"
)

model_data = [
    (
        "uk_ctrl_um",
        "/data/scratch/byron.blay/RES_RETRIEVAL_CACHE/test_lfric/20240121T0000Z/uk_ctrl_um/20240121T0000Z_UK_672x672_1km_RAL3P3_pdiag*.pp",
    ),
    (
        "uk_expt_lfric",
        "/data/scratch/byron.blay/RES_RETRIEVAL_CACHE/test_lfric/20240121T0000Z/uk_expt_lfric/20240121T0000Z_UK_672x672_1km_RAL3P3_lfric*.nc",
    ),
]

vars = [
    "surface_microphysical_rainfall_rate",  # m01s04i203
    "surface_microphysical_rainfall_amount",  # m01s04i201
]

# todo: it's inefficient to keep reloading the data for each var/cell_attribute/time_grouping
#  it would seem to be better to send the list of vars to the operator and plot functions, just once.
for var in vars:
    print(f"\nrunning recipe for {var}\n" )

    recipe_variables = {
        "INPUT_PATHS": [i[1] for i in model_data],
        "MODEL_NAMES": [i[0] for i in model_data],
        "VARNAME": var,
        "OUTPUT_FOLDER": "/data/scratch/byron.blay/cset/cell_stats/out4",
    }

    recipe = parse_recipe(recipe_fpath, recipe_variables)
    execute_recipe(recipe, Path(__file__).parent)
