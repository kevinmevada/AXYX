"""Read-only helpers for MATLAB Dat structs loaded via SciPy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from scipy.io import loadmat, whosmat


def load_dat(path: Path, *, variable: str = "Dat") -> Any:
    mat = loadmat(
        str(path),
        struct_as_record=False,
        squeeze_me=True,
        variable_names=[variable],
    )
    if variable not in mat:
        raise KeyError(f"{path} does not contain variable {variable!r}")
    return mat[variable]


def mat_info(path: Path) -> list[tuple[str, tuple[int, ...], str]]:
    return list(whosmat(str(path)))


def fieldnames(obj: Any) -> list[str]:
    names = getattr(obj, "_fieldnames", None)
    if names is None:
        return []
    return list(names)


def has_field(obj: Any, name: str) -> bool:
    return name in fieldnames(obj)


def get_field(obj: Any, name: str) -> Any:
    return getattr(obj, name)


def is_struct(obj: Any) -> bool:
    return hasattr(obj, "_fieldnames")


def is_numeric_array(obj: Any) -> bool:
    return isinstance(obj, np.ndarray) and obj.dtype != object and np.issubdtype(obj.dtype, np.number)


def subject_fields(dat: Any) -> list[str]:
    names = []
    for name in fieldnames(dat):
        if name.startswith("S") and name[1:].isdigit():
            names.append(name)
    return sorted(names, key=lambda n: int(n[1:]))


def subject_id_from_field(name: str) -> int:
    return int(name[1:])
