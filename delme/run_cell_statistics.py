from pathlib import Path

from CSET._common import parse_recipe
from CSET.operators import execute_recipe

cell_attributes =['effective_radius_in_km', 'mean_value']

recipe_fpath = Path(__file__).parent.parent / "src" / "CSET" / "recipes" / "cell_statistics.yaml"

# model_data = [
#     ('uk_ctrl_um', '/data/scratch/byron.blay/RES_RETRIEVAL_CACHE/test_lfric/20240121T0000Z/uk_ctrl_um/20240121T0000Z_UK_672x672_1km_RAL3P3_pdiagb000.pp'),
#     ('uk_ctrl_um', '/data/scratch/byron.blay/RES_RETRIEVAL_CACHE/test_lfric/20240121T0000Z/uk_ctrl_um/20240121T0000Z_UK_672x672_1km_RAL3P3_pdiagb012.pp'),
#     ('uk_expt_lfric', '/data/scratch/byron.blay/RES_RETRIEVAL_CACHE/test_lfric/20240121T0000Z/uk_expt_lfric/20240121T0000Z_UK_672x672_1km_RAL3P3_lfric_slam_timeproc_000_006.nc'),
#     ('uk_expt_lfric', '/data/scratch/byron.blay/RES_RETRIEVAL_CACHE/test_lfric/20240121T0000Z/uk_expt_lfric/20240121T0000Z_UK_672x672_1km_RAL3P3_lfric_slam_timeproc_006_012.nc'),
# ]

model_data = [
    ('uk_ctrl_um', '/data/scratch/byron.blay/RES_RETRIEVAL_CACHE/test_lfric/20240121T0000Z/uk_ctrl_um/20240121T0000Z_UK_672x672_1km_RAL3P3_pdiag*.pp'),
    ('uk_expt_lfric', '/data/scratch/byron.blay/RES_RETRIEVAL_CACHE/test_lfric/20240121T0000Z/uk_expt_lfric/20240121T0000Z_UK_672x672_1km_RAL3P3_lfric*.nc'),
]


vars = [
    'surface_microphysical_rainfall_amount',  # m01s04i201
    'surface_microphysical_rainfall_rate',  # m01s04i203 todo: seems to have missing data, needs investigation
]

time_groupings = ['forecast_period', 'hour']


# # DEBUG
# import CSET.operators.cell_statistics as cell_statistics
# cell_statistics.caller_thing(cubes=None, cell_attribute='effective_radius_in_km', time_grouping='forecast_period')
# exit(0)


for cell_attribute in cell_attributes:
    for var in vars:
        for time_grouping in time_groupings:
            recipe_variables = {
                'INPUT_PATHS': [i[1] for i in model_data],
                'MODEL_NAMES': [i[0] for i in model_data],
                'VARNAME': var,
                'CELL_ATTRIBUTE': cell_attribute,
                'TIME_GROUPING': time_grouping,
            }

            recipe = parse_recipe(recipe_fpath, recipe_variables)
            execute_recipe(recipe, Path(__file__).parent)
