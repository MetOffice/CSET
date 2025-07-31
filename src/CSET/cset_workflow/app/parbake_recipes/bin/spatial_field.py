"""Construct all the recipes."""

import itertools

from .parbake_all import RecipeList, get_models


# Generate recipes.
def recipes(v: dict) -> RecipeList:
    """Generate recipes from the given suite configuration."""
    recipes = RecipeList()

    # Load a list of model detail dictionaries.
    models = get_models(v)

    # Surface (2D) fields.
    if v["SPATIAL_SURFACE_FIELD"]:
        for model, field, method in itertools.product(
            models, v["SURFACE_FIELDS"], v["SPATIAL_SURFACE_FIELD_METHOD"]
        ):
            recipes.add(
                recipe="generic_surface_spatial_plot_sequence.yaml",
                model_ids=model["id"],
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": model["name"],
                    "METHOD": method,
                    "SUBAREA_TYPE": v["SUBAREA_TYPE"] if v["SELECT_SUBAREA"] else None,
                    "SUBAREA_EXTENT": v["SUBAREA_EXTENT"]
                    if v["SELECT_SUBAREA"]
                    else None,
                },
                aggregation=False,
            )

    # Pressure level fields.
    if v["SPATIAL_PLEVEL_FIELD"]:
        for model, field, plevel, method in itertools.product(
            models,
            v["PRESSURE_LEVEL_FIELDS"],
            v["PRESSURE_LEVELS"],
            v["SPATIAL_PLEVEL_FIELD_METHOD"],
        ):
            recipes.add(
                recipe="generic_level_spatial_plot_sequence.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "pressure",
                    "LEVEL": plevel,
                    "MODEL_NAME": model["name"],
                    "METHOD": method,
                    "SUBAREA_TYPE": v["SUBAREA_TYPE"] if v["SELECT_SUBAREA"] else None,
                    "SUBAREA_EXTENT": v["SUBAREA_EXTENT"]
                    if v["SELECT_SUBAREA"]
                    else None,
                },
                model_ids=model["id"],
                aggregation=False,
            )

    # Model level fields
    if v["SPATIAL_MLEVEL_FIELD"]:
        for model, field, mlevel, method in itertools.product(
            models,
            v["MODEL_LEVEL_FIELDS"],
            v["MODEL_LEVELS"],
            v["SPATIAL_MLEVEL_FIELD_METHOD"],
        ):
            recipes.add(
                recipe="generic_level_spatial_plot_sequence.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "model_level_number",
                    "LEVEL": mlevel,
                    "MODEL_NAME": model["name"],
                    "METHOD": method,
                    "SUBAREA_TYPE": v["SUBAREA_TYPE"] if v["SELECT_SUBAREA"] else None,
                    "SUBAREA_EXTENT": v["SUBAREA_EXTENT"]
                    if v["SELECT_SUBAREA"]
                    else None,
                },
                model_ids=model["id"],
                aggregation=False,
            )

    # Case aggregation.

    # Create a list of case aggregation types.
    AGGREGATION_TYPES = ["LEAD_TIME", "HOUR_OF_DAY", "VALIDITY_TIME", "ALL"]

    # Surface (2D) fields.
    for model, atype, field in itertools.product(
        models, range(len(AGGREGATION_TYPES)), v["SURFACE_FIELDS"]
    ):
        if v["SPATIAL_SURFACE_FIELD_AGGREGATION"][atype]:
            recipes.add(
                recipe=f"generic_surface_spatial_plot_sequence_case_aggregation_mean_{AGGREGATION_TYPES[atype].lower()}.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": model["name"],
                    "SUBAREA_TYPE": v["SUBAREA_TYPE"] if v["SELECT_SUBAREA"] else None,
                    "SUBAREA_EXTENT": v["SUBAREA_EXTENT"]
                    if v["SELECT_SUBAREA"]
                    else None,
                },
                model_ids=model["id"],
                aggregation=True,
            )

    # Pressure level fields.
    for model, atype, field, plevel in itertools.product(
        models,
        range(len(AGGREGATION_TYPES)),
        v["PRESSURE_LEVEL_FIELDS"],
        v["PRESSURE_LEVELS"],
    ):
        if v["SPATIAL_PLEVEL_FIELD_AGGREGATION"][atype]:
            recipes.add(
                recipe=f"generic_level_spatial_plot_sequence_case_aggregation_mean_{AGGREGATION_TYPES[atype].lower()}.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "pressure",
                    "LEVEL": plevel,
                    "MODEL_NAME": model["name"],
                    "SUBAREA_TYPE": v["SUBAREA_TYPE"] if v["SELECT_SUBAREA"] else None,
                    "SUBAREA_EXTENT": v["SUBAREA_EXTENT"]
                    if v["SELECT_SUBAREA"]
                    else None,
                },
                model_ids=model["id"],
                aggregation=True,
            )

    # Model level fields.
    for model, atype, field, mlevel in itertools.product(
        models,
        range(len(AGGREGATION_TYPES)),
        v["MODEL_LEVEL_FIELDS"],
        v["MODEL_LEVELS"],
    ):
        if v["SPATIAL_MLEVEL_FIELD_AGGREGATION"][atype]:
            recipes.add(
                recipe=f"generic_level_spatial_plot_sequence_case_aggregation_mean_{AGGREGATION_TYPES[atype].lower()}.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "model_level_number",
                    "LEVEL": mlevel,
                    "MODEL_NAME": model["name"],
                    "SUBAREA_TYPE": v["SUBAREA_TYPE"] if v["SELECT_SUBAREA"] else None,
                    "SUBAREA_EXTENT": v["SUBAREA_EXTENT"]
                    if v["SELECT_SUBAREA"]
                    else None,
                },
                model_ids=model["id"],
                aggregation=True,
            )

    return recipes
