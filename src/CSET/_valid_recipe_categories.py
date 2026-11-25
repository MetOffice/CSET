CATEGORIES = frozenset({"diagnostics", "observations", "verification"})
PLOT_TYPES = frozenset(
    {
        "spatial",
        "time series",
        "histogram",
        "power spectrum",
        "transect",
        "transect difference",
        "structural similarity",
        "spatial difference",
        "vertical profile",
        "scatter plot",
        "vector plot",
        "multivariable spatial",
        "quantile-quantile",
    }
)
LEVEL_TYPES = frozenset({"model", "pressure", "surface", "$LEVELTYPE"})
ENSEMBLE = frozenset({"true", "false"})
DERIVED = frozenset({"true", "false"})
OBSERVATION_TYPES = frozenset({"nimrod", "point", "cardington"})
AGGREGATION_TYPES = frozenset({"all", "hour of day", "validity time", "lead time"})

ENFORCED_RECIPE_METADATA = {}
# metadata in recipes that we wish to enforce

VALID_LEVEL_TYPES = {"PRESSURE": "pressure", "MODEL": "model", "SURFACE": "surface"}

DEFAULT_METADATA = {
    "level_type": "unknown",
    "aggregation_type": "none",
    "ensembles": "false",
    "observation_type": "none",
    "derived": "false",
    "plot_type": "unknown",
}

ENFORCED_METADATA = {
    "category": CATEGORIES,
    "plot_type": PLOT_TYPES | {DEFAULT_METADATA["plot_type"]},
    "level_type": LEVEL_TYPES | {DEFAULT_METADATA["level_type"]},
    "aggregation_type": AGGREGATION_TYPES | {DEFAULT_METADATA["aggregation_type"]},
    "ensembles": ENSEMBLE | {DEFAULT_METADATA["ensembles"]},
    "derived": DERIVED | {DEFAULT_METADATA["derived"]},
    "observation_type": OBSERVATION_TYPES | {DEFAULT_METADATA["observation_type"]},
}


REQUIRED_KEYS = frozenset({"category"})


def validate_metadata(meta: dict) -> None:
    missing = REQUIRED_KEYS - meta.keys()
    if missing:
        raise ValueError(f"Missing required metadata: {sorted(missing)}")
    for key, allowed in ENFORCED_METADATA.items():
        value = meta.get(key, DEFAULT_METADATA.get(key))
        if value is not None and value not in allowed:
            raise ValueError(f"{key}={value!r} not in {sorted(allowed)}")
