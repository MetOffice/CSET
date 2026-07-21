"""
Tools for reading BOM system data.

Internal BOM systems use PrepBom as a base class and fill in the internal
patterns.
"""

from typing import Iterable

from metomi.isodatetime.data import TimePoint
from pandas import DataFrame

from .odb2 import PrepODB2, read_file, read_tarfile

# Valid bureau forecast systems
BOM_SYSTEMS = ["access_g3", "access_g4"]
for dm in ["ad", "bn", "dn", "nq", "ph", "sy", "vt"]:
    BOM_SYSTEMS.extend(["access_c3_" + dm, "access_c4_" + dm])

# ODB files to read for each system
access_c_types = ["aircraftsondesurface"]
access_g_types = ["aircraft", "sonde", "surface"]


class PrepBom(PrepODB2):
    """Prepare Bureau ODB2 data for MET."""

    def __init__(self, system: str):
        """
        Create the converter.

        Args:
            system: BOM system to source observations from (e.g. 'access_c3_dn')
        """
        self.system = system

    def read_c3_type(self, type: str, valid_time: TimePoint) -> Iterable[DataFrame]:
        """Read C3 data pattern."""
        raise NotImplementedError

    def read_c4_type(self, type: str, valid_time: TimePoint) -> Iterable[DataFrame]:
        """Read C4 data pattern."""
        raise NotImplementedError

    def read_g3_type(self, type: str, valid_time: TimePoint) -> Iterable[DataFrame]:
        """Read G3 data pattern."""
        raise NotImplementedError

    def read_g4_type(self, type: str, valid_time: TimePoint) -> Iterable[DataFrame]:
        """Read G4 data pattern."""
        raise NotImplementedError

    def read_type(self, type: str, valid_time: TimePoint) -> Iterable[DataFrame]:
        """
        Dispatch to readers for the current system.

        Args:
            type: observation type (ODB2 file name without the suffix)
            valid_time: time to load

        Returns an iterable of ODB2 DataFrames
        """
        if self.system.startswith("access_c3"):
            yield from self.read_c3_type(type, valid_time)
        elif self.system.startswith("access_c4"):
            yield from self.read_c4_type(type, valid_time)
        elif self.system.startswith("access_g3"):
            yield from self.read_g3_type(type, valid_time)
        elif self.system.startswith("access_g4"):
            yield from self.read_g4_type(type, valid_time)

    def read_odb(self, valid_time: TimePoint) -> Iterable[DataFrame]:
        """
        Read in the ODB2 files that we use with MET.

        Args:
            valid_time: time to load

        Returns an iterable of ODB2 DataFrames
        """
        if self.system.startswith("access_c"):
            for type in access_c_types:
                yield from self.read_type(type, valid_time)

        elif self.system.startswith("access_g"):
            for type in access_g_types:
                yield from self.read_type(type, valid_time)

        else:
            raise ValueError("Unknown system '%s'", self.system)


class PrepBomNci(PrepBom):
    """Read BOM data stored at NCI."""

    def __init__(self, system: str):
        """
        Create the converter.

        Args:
            system: BOM system to source observations from (e.g. 'access_c3_dn')
        """
        super().__init__(system)

    def read_c3_type(self, type: str, valid_time: TimePoint) -> Iterable[DataFrame]:
        """Read C3 data pattern."""
        domain = self.system.split("_")[-1]
        tarfile = f"/g/data/ig2/odb2/access_c3/%Y/%m/%Y%m%dT%H%MZ/%Y%m%dT%H%MZ_{domain}_odb2.tar.zst"
        obsfile = f"ukv_odb2/{type}.odb"
        return read_tarfile(tarfile, obsfile, valid_time)

    def read_c4_type(self, type: str, valid_time: TimePoint) -> Iterable[DataFrame]:
        """Read C4 data pattern."""
        domain = self.system.split("_")[-1]
        tarfile = f"/g/data/ig2/odb2/access_c4/%Y/%m/%Y%m%dT%H%MZ/%Y%m%dT%H%MZ_{domain}_odb2.tgz"
        obsfile = f"ukv_odb2/{type}.odb"
        return read_tarfile(tarfile, obsfile, valid_time)

    def read_g3_type(self, type: str, valid_time: TimePoint) -> Iterable[DataFrame]:
        """Read G3 data pattern."""
        pattern = (
            "/g/data/ig2/odb2/access_g3/%Y/%m/%Y%m%dT%H%MZ/glm_odb2/{type}.odb.zst"
        )
        return read_file(pattern, valid_time)

    def read_g4_type(self, type: str, valid_time: TimePoint) -> Iterable[DataFrame]:
        """Read G4 data pattern."""
        pattern = (
            "/g/data/ig2/odb2/access_g4/%Y/%m/%Y%m%dT%H%MZ/glm_odb2/{type}.odb.zst"
        )
        return read_file(pattern, valid_time)
