#! /usr/bin/env python3

"""Functions to create style file with model:color mapping."""

import itertools
import json
import os

# matplotlib tab20[::2] + tab20[1::2]
DISCRETE_COLORS = (
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
    "#aec7e8",
    "#ffbb78",
    "#98df8a",
    "#ff9896",
    "#c5b0d5",
    "#c49c94",
    "#f7b6d2",
    "#c7c7c7",
    "#dbdb8d",
    "#9edae5",
)


def create_model_colour_mapping(model_names: list[str]) -> dict:
    """
    Create dict with model name <-> colour mapping.

    The model names are mapped to colours in alphabetical order.

    Arguments
    ---------
    model_names: list[str]
        List of names of the models to be mapped to color

    Returns
    -------
    model_color_map: dict
        Dictionary of model_name: colour mappings.
    """
    # Repeat colours if we have more than 20 models. We probably don't care
    # about individual models in that case.
    infinite_colours = itertools.chain.from_iterable(itertools.repeat(DISCRETE_COLORS))
    return {
        model: color
        for model, color in zip(sorted(model_names), infinite_colours, strict=False)
    }


def main():
    """Create model name <-> colour mappings add to a copy of the style file."""
    model_names = os.environ["MODELS"].splitlines()
    style_file = os.getenv("COLORBAR_FILE")

    if style_file:
        with open(style_file, "rt") as fp:
            style = json.load(fp)
    else:
        style = {}

    style["model_colors"] = create_model_colour_mapping(model_names)

    with open(f"{os.environ['CYLC_WORKFLOW_SHARE_DIR']}/style.json", "wt") as fp:
        json.dump(style, fp, indent=2)


if __name__ == "__main__":
    main()
