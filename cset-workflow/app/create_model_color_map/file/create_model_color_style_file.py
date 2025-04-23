"""Functions to create style file with model:color mapping."""

import argparse
import json

# matplotlib tab20[::2] + tab20[1::2]
DISCRETE_COLORS = [
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
]


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--models",
        dest="models",
        type=str,
        nargs="+",
        help="list of models to map colors to",
    )
    parser.add_argument(
        "-f",
        "--filepath",
        dest="filepath",
        type=str,
        help="full path to output json file or to a json file to be appended to",
    )
    parser.add_argument(
        "-a",
        "--append",
        dest="append",
        action="store_true",
        help="if -a/--append flag is specified model:colr mapping is appended to the file "
        "specified with a filepath",
    )
    return parser.parse_args()


def create_model_color_map(model_names: list[str]) -> dict:
    """
    Create dict with model:color mapping.

    Arguments
    ---------
    model_names: list
        List of names of the models to be mapped to color

    Returns
    -------
    model_color_map: dict
        Dictionary with model:color mapping.

    """
    color_list = DISCRETE_COLORS
    while len(model_names) > len(color_list):
        color_list += color_list

    return {
        mname: color
        for mname, color in zip(sorted(model_names), color_list, strict=False)
    }


def create_json_file(input: dict, filepath: str, append: bool) -> None:
    """
    Create json file that contains the model:color mapping.

    Arguments
    ---------
    input: dict
        Dictionary with model:color mapping.
    filepath: str
        Full path to output json file or to a json file to be appended to
    append: bool
        If True, model:color mapping is appended to preexisting json file

    Raises
    ------
    FileNotFoundError
       If append is True and the provided path does not exist
    """
    base = {}
    if append:
        try:
            with open(filepath, "r") as fp:
                base = json.load(fp)
        except FileNotFoundError as err:
            raise FileNotFoundError(f"File {filepath} not found.") from err
    base.update(input)

    with open(filepath, "w+") as fp:
        json.dump(base, fp, indent=4)


def main():
    """Create model:color mapping and save to json file."""
    args = parse_arguments()
    model_color_map = create_model_color_map(args.models)
    create_json_file(model_color_map, args.filepath, args.append)


if __name__ == "__main__":
    main()
