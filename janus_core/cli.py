"""Set up commandline interface."""

import ast
from pathlib import Path
from typing import Annotated

import typer

from janus_core.geom_opt import optimize
from janus_core.single_point import SinglePoint

app = typer.Typer()


class TyperDict:  #  pylint: disable=too-few-public-methods
    """
    Custom dictionary for typer.

    Parameters
    ----------
    value : str
        Value of string representing a dictionary.
    """

    def __init__(self, value: str):
        """
        Initialise class.

        Parameters
        ----------
        value : str
            Value of string representing a dictionary.
        """
        self.value = value

    def __str__(self):
        """
        String representation of class.

        Returns
        -------
        str
            Class name and value of string representing a dictionary.
        """
        return f"<TyperDict: value={self.value}>"


def parse_dict_class(value: str):
    """
    Convert string input into a dictionary.

    Parameters
    ----------
    value : str
        String representing dictionary to be parsed.

    Returns
    -------
    TyperDict
        Parsed string as a dictionary.
    """
    return TyperDict(ast.literal_eval(value))


def parse_typer_dicts(typer_dicts: list[TyperDict]) -> list[dict]:
    """
    Convert list of TyperDict objects to list of dictionaries.

    Parameters
    ----------
    typer_dicts : list[TyperDict]
        List of TyperDict objects to convert.

    Returns
    -------
    list[dict]
        List of converted dictionaries.

    Raises
    ------
    ValueError
        If items in list are not converted to dicts.
    """
    for i, typer_dict in enumerate(typer_dicts):
        typer_dicts[i] = typer_dict.value if typer_dict else {}
        if not isinstance(typer_dicts[i], dict):
            raise ValueError(f"{typer_dicts[i]} must be passed as a dictionary")
    return typer_dicts


# Shared type aliases
StructPath = Annotated[
    Path, typer.Option("--struct", help="Path of structure to simulate")
]
Architecture = Annotated[
    str, typer.Option("--arch", help="MLIP architecture to use for calculations")
]
Device = Annotated[str, typer.Option(help="Device to run calculations on")]
ReadKwargs = Annotated[
    TyperDict,
    typer.Option(
        parser=parse_dict_class,
        help="Keyword arguments to pass to ase.io.read  [default: {}]",
        metavar="DICT",
    ),
]
CalcKwargs = Annotated[
    TyperDict,
    typer.Option(
        parser=parse_dict_class,
        help=(
            "Keyword arguments to pass to selected calculator. For the default "
            "architecture ('mace_mp'), {'model':'small'} is set by default  "
            "[default: {}]"
        ),
        metavar="DICT",
    ),
]
WriteKwargs = Annotated[
    TyperDict,
    typer.Option(
        parser=parse_dict_class,
        help=(
            "Keyword arguments to pass to ase.io.write when saving "
            "results  [default: {}]"
        ),
        metavar="DICT",
    ),
]
LogFile = Annotated[Path, typer.Option("--log", help="Path to save logs to")]


@app.command()
def singlepoint(
    struct_path: StructPath,
    architecture: Architecture = "mace_mp",
    device: Device = "cpu",
    properties: Annotated[
        list[str],
        typer.Option(
            "--property",
            help=(
                "Properties to calculate. If not specified, 'energy', 'forces' "
                "and 'stress' will be returned."
            ),
        ),
    ] = None,
    read_kwargs: ReadKwargs = None,
    calc_kwargs: CalcKwargs = None,
    write_kwargs: WriteKwargs = None,
    log_file: LogFile = "singlepoint.log",
):
    """
    Perform single point calculations and save to file.

    Parameters
    ----------
    struct_path : Path
        Path of structure to simulate.
    architecture : Optional[str]
        MLIP architecture to use for single point calculations.
        Default is "mace_mp".
    device : Optional[str]
        Device to run model on. Default is "cpu".
    properties : Optional[str]
        Physical properties to calculate. Default is "energy".
    read_kwargs : Optional[dict[str, Any]]
        Keyword arguments to pass to ase.io.read. Default is {}.
    calc_kwargs : Optional[dict[str, Any]]
        Keyword arguments to pass to the selected calculator. Default is {}.
    write_kwargs : Optional[dict[str, Any]]
        Keyword arguments to pass to ase.io.write when saving results. Default is {}.
    log_file : Optional[Path]
        Path to write logs to. Default is "singlepoint.log".
    """
    [read_kwargs, calc_kwargs, write_kwargs] = parse_typer_dicts(
        [read_kwargs, calc_kwargs, write_kwargs]
    )

    s_point = SinglePoint(
        struct_path=struct_path,
        architecture=architecture,
        device=device,
        read_kwargs=read_kwargs,
        calc_kwargs=calc_kwargs,
        log_kwargs={"filename": log_file, "filemode": "w"},
    )
    s_point.run(properties=properties, write_results=True, write_kwargs=write_kwargs)


@app.command()
def geomopt(  # pylint: disable=too-many-arguments,too-many-locals
    struct_path: StructPath,
    fmax: Annotated[
        float, typer.Option("--max-force", help="Maximum force for convergence")
    ] = 0.1,
    steps: Annotated[
        int, typer.Option("--steps", help="Maximum number of optimization steps")
    ] = 1000,
    architecture: Architecture = "mace_mp",
    device: Device = "cpu",
    fully_opt: Annotated[
        bool,
        typer.Option(
            "--fully-opt",
            help="Fully optimize the cell vectors, angles, and atomic positions",
        ),
    ] = False,
    vectors_only: Annotated[
        bool,
        typer.Option(
            "--vectors-only",
            help=(
                "Disable optimizing cell angles, so only cell vectors and atomic "
                "positions are optimized. Requires --fully-opt to be set"
            ),
        ),
    ] = False,
    read_kwargs: ReadKwargs = None,
    calc_kwargs: CalcKwargs = None,
    opt_kwargs: Annotated[
        TyperDict,
        typer.Option(
            parser=parse_dict_class,
            help=("Keyword arguments to pass to optimizer  [default: {}]"),
            metavar="DICT",
        ),
    ] = None,
    write_kwargs: WriteKwargs = None,
    traj_file: Annotated[
        str, typer.Option("--traj", help="Path to save optimization frames to")
    ] = None,
    log_file: LogFile = "geomopt.log",
):
    """
    Perform geometry optimization and save optimized structure to file.

    Parameters
    ----------
    struct_path : Path
        Path of structure to simulate.
    fmax : float
        Set force convergence criteria for optimizer in units eV/Å.
        Default is 0.1.
    steps : int
        Set maximum number of optimization steps to run. Default is 1000.
    architecture : Optional[str]
        MLIP architecture to use for geometry optimization.
        Default is "mace_mp".
    device : Optional[str]
        Device to run model on. Default is "cpu".
    fully_opt : bool
        Whether to optimize the cell as well as atomic positions. Default is False.
    vectors_only : bool
        Whether to allow only hydrostatic deformations. Default is False.
    read_kwargs : Optional[dict[str, Any]]
        Keyword arguments to pass to ase.io.read. Default is {}.
    calc_kwargs : Optional[dict[str, Any]]
        Keyword arguments to pass to the selected calculator. Default is {}.
    opt_kwargs : Optional[ASEOptArgs]
        Keyword arguments to pass to optimizer. Default is {}.
    write_kwargs : Optional[ASEWriteArgs]
        Keyword arguments to pass to ase.io.write when saving optimized structure.
        Default is {}.
    traj_file : Optional[str]
        Path to save optimization trajectory to. Default is None.
    log_file : Optional[Path]
        Path to write logs to. Default is "geomopt.log".
    """
    [read_kwargs, calc_kwargs, opt_kwargs, write_kwargs] = parse_typer_dicts(
        [read_kwargs, calc_kwargs, opt_kwargs, write_kwargs]
    )

    if not fully_opt and vectors_only:
        raise ValueError("--vectors-only requires --fully-opt to be set")

    # Set up single point calculator
    s_point = SinglePoint(
        struct_path=struct_path,
        architecture=architecture,
        device=device,
        read_kwargs=read_kwargs,
        calc_kwargs=calc_kwargs,
        log_kwargs={"filename": log_file, "filemode": "w"},
    )

    # Check trajectory not duplicated
    if "trajectory" in opt_kwargs:
        raise ValueError("'trajectory' must be passed through the --traj option")

    # Set same name to overwrite saved binary with xyz
    opt_kwargs["trajectory"] = traj_file if traj_file else None
    traj_kwargs = {"filename": traj_file} if traj_file else None

    filter_kwargs = {"hydrostatic_strain": vectors_only} if fully_opt else None

    # Use default filter if passed --fully-opt, otherwise override with None
    fully_opt_dict = {} if fully_opt else {"filter_func": None}

    # Run geometry optimization and save output structure
    optimize(
        s_point.struct,
        fmax=fmax,
        steps=steps,
        filter_kwargs=filter_kwargs,
        **fully_opt_dict,
        opt_kwargs=opt_kwargs,
        write_results=True,
        write_kwargs=write_kwargs,
        traj_kwargs=traj_kwargs,
        log_kwargs={"filename": log_file, "filemode": "a"},
    )
