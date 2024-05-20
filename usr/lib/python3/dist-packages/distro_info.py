# Copyright (C) 2009-2012, Benjamin Drung <bdrung@debian.org>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""provides information about Ubuntu's and Debian's distributions"""

import csv
import datetime
import os
import typing


def convert_date(string: str) -> datetime.date:
    """Convert a date string in ISO 8601 into a datetime object."""
    parts = [int(x) for x in string.split("-")]
    if len(parts) == 3:
        (year, month, day) = parts
        return datetime.date(year, month, day)
    if len(parts) == 2:
        (year, month) = parts
        if month == 12:
            return datetime.date(year, month, 31)
        return datetime.date(year, month + 1, 1) - datetime.timedelta(1)
    raise ValueError("Date not in ISO 8601 format.")


def _get_data_dir() -> str:
    """Get the data directory based on the module location."""
    return "/usr/share/distro-info"


class DistroDataOutdated(Exception):
    """Distribution data outdated."""

    def __init__(self) -> None:
        super().__init__(
            "Distribution data outdated. Please check for an update for distro-info-data. "
            "See /usr/share/doc/distro-info-data/README.Debian for details."
        )


class DistroRelease:
    """Represents a distributions release"""

    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        version: str,
        codename: str,
        series: str,
        created: datetime.date,
        release: typing.Optional[datetime.date] = None,
        eol: typing.Optional[datetime.date] = None,
        eol_esm: typing.Optional[datetime.date] = None,
        eol_lts: typing.Optional[datetime.date] = None,
        eol_elts: typing.Optional[datetime.date] = None,
        eol_server: typing.Optional[datetime.date] = None,
    ) -> None:
        # pylint: disable=too-many-arguments
        self.version = version
        self.codename = codename
        self.series = series
        self.created = created
        self.release = release
        self.eol = eol
        self.eol_lts = eol_lts
        self.eol_elts = eol_elts
        self.eol_esm = eol_esm
        self.eol_server = eol_server

    def is_supported(self, date: datetime.date) -> bool:
        """Check whether this release is supported on the given date."""
        return date >= self.created and (
            self.eol is None
            or date <= self.eol
            or (self.eol_server is not None and date <= self.eol_server)
        )


def _get_date(row: dict[str, str], column: str) -> typing.Optional[datetime.date]:
    date_string = row.get(column)
    if not date_string:
        return None
    return convert_date(date_string)


class DistroInfo:
    """Base class for distribution information.
    Use DebianDistroInfo or UbuntuDistroInfo instead of using this directly.
    """

    def __init__(self, distro: str) -> None:
        self._distro = distro
        filename = os.path.join(_get_data_dir(), distro.lower() + ".csv")
        with open(filename, encoding="utf-8") as csvfile:
            csv_reader = csv.DictReader(csvfile)
            self._releases = []
            for row in csv_reader:
                release = DistroRelease(
                    row["version"],
                    row["codename"],
                    row["series"],
                    convert_date(row["created"]),
                    _get_date(row, "release"),
                    _get_date(row, "eol"),
                    _get_date(row, "eol-esm"),
                    _get_date(row, "eol-lts"),
                    _get_date(row, "eol-elts"),
                    _get_date(row, "eol-server"),
                )
                self._releases.append(release)
        self._date = datetime.date.today()

    @property
    def all(self) -> list[str]:
        """List codenames of all known distributions."""
        return [x.series for x in self._releases]

    def get_all(self, result: str = "codename") -> list[typing.Union[DistroRelease, str]]:
        """List all known distributions."""
        return [self._format(result, x) for x in self._releases]

    def _avail(self, date: datetime.date) -> list[DistroRelease]:
        """Return all distributions that were available on the given date."""
        return [x for x in self._releases if date >= x.created]

    def codename(
        self,
        release: str,
        date: typing.Optional[datetime.date] = None,
        default: typing.Optional[str] = None,
    ) -> typing.Union[DistroRelease, str, None]:
        """Map codename aliases to the codename they describe."""
        # pylint: disable=no-self-use,unused-argument
        return release

    def version(self, name: str, default: typing.Optional[str] = None) -> typing.Optional[str]:
        """Map codename or series to version"""
        for release in self._releases:
            if name in (release.codename, release.series):
                return release.version
        return default

    def devel(
        self, date: typing.Optional[datetime.date] = None, result: str = "codename"
    ) -> typing.Union[DistroRelease, str]:
        """Get latest development distribution based on the given date."""
        if date is None:
            date = self._date
        distros = [
            x
            for x in self._avail(date)
            if x.release is None or (date < x.release and (x.eol is None or date <= x.eol))
        ]
        if not distros:
            raise DistroDataOutdated()
        return self._format(result, distros[-1])

    def _format(
        self, format_string: str, release: DistroRelease
    ) -> typing.Union[DistroRelease, str]:
        """Format a given distribution entry."""
        if format_string == "object":
            return release
        if format_string == "codename":
            return release.series
        if format_string == "fullname":
            return self._distro + " " + release.version + ' "' + release.codename + '"'
        if format_string == "release":
            return release.version

        raise ValueError(
            "Only codename, fullname, object, and release are allowed "
            "result values, but not '" + format_string + "'."
        )

    def stable(
        self, date: typing.Optional[datetime.date] = None, result: str = "codename"
    ) -> typing.Union[DistroRelease, str]:
        """Get latest stable distribution based on the given date."""
        if date is None:
            date = self._date
        distros = [
            x
            for x in self._avail(date)
            if x.release is not None and date >= x.release and (x.eol is None or date <= x.eol)
        ]
        if not distros:
            raise DistroDataOutdated()
        return self._format(result, distros[-1])

    def supported(
        self, date: typing.Optional[datetime.date] = None, result: str = "codename"
    ) -> list[typing.Union[DistroRelease, str]]:
        """Get list of all supported distributions based on the given date."""
        raise NotImplementedError()

    def valid(self, codename: str) -> bool:
        """Check if the given codename is known."""
        return codename in self.all

    def unsupported(
        self, date: typing.Optional[datetime.date] = None, result: str = "codename"
    ) -> list[typing.Union[DistroRelease, str]]:
        """Get list of all unsupported distributions based on the given date."""
        if date is None:
            date = self._date
        supported = self.supported(date)
        distros = [self._format(result, x) for x in self._avail(date) if x.series not in supported]
        return distros


class DebianDistroInfo(DistroInfo):
    """provides information about Debian's distributions"""

    def __init__(self) -> None:
        super().__init__("Debian")

    def codename(
        self,
        release: str,
        date: typing.Optional[datetime.date] = None,
        default: typing.Optional[str] = None,
    ) -> typing.Union[DistroRelease, str, None]:
        """Map 'unstable', 'testing', etc. to their codenames."""
        if release == "unstable":
            return self.devel(date)
        if release == "testing":
            return self.testing(date)
        if release == "stable":
            return self.stable(date)
        if release == "oldstable":
            return self.old(date)
        return default

    def devel(
        self, date: typing.Optional[datetime.date] = None, result: str = "codename"
    ) -> typing.Union[DistroRelease, str]:
        """Get latest development distribution based on the given date."""
        if date is None:
            date = self._date
        distros = [
            x
            for x in self._avail(date)
            if x.release is None or (date < x.release and (x.eol is None or date <= x.eol))
        ]
        if len(distros) < 2:
            raise DistroDataOutdated()
        return self._format(result, distros[-2])

    def old(
        self, date: typing.Optional[datetime.date] = None, result: str = "codename"
    ) -> typing.Union[DistroRelease, str]:
        """Get old (stable) Debian distribution based on the given date."""
        if date is None:
            date = self._date
        distros = [x for x in self._avail(date) if x.release is not None and date >= x.release]
        if len(distros) < 2:
            raise DistroDataOutdated()
        return self._format(result, distros[-2])

    def supported(
        self, date: typing.Optional[datetime.date] = None, result: str = "codename"
    ) -> list[typing.Union[DistroRelease, str]]:
        """Get list of all supported Debian distributions based on the given
        date."""
        if date is None:
            date = self._date
        distros = [
            self._format(result, x) for x in self._avail(date) if x.eol is None or date <= x.eol
        ]
        return distros

    def lts_supported(
        self, date: typing.Optional[datetime.date] = None, result: str = "codename"
    ) -> list[typing.Union[DistroRelease, str]]:
        """Get list of all LTS supported Debian distributions based on the given
        date."""
        if date is None:
            date = self._date
        distros = [
            self._format(result, x)
            for x in self._avail(date)
            if (x.eol is not None and date > x.eol)
            and (x.eol_lts is not None and date <= x.eol_lts)
        ]
        return distros

    def elts_supported(
        self, date: typing.Optional[datetime.date] = None, result: str = "codename"
    ) -> list[typing.Union[DistroRelease, str]]:
        """Get list of all Extended LTS supported Debian distributions based on
        the given date."""
        if date is None:
            date = self._date
        distros = [
            self._format(result, x)
            for x in self._avail(date)
            if (x.eol_lts is not None and date > x.eol_lts)
            and (x.eol_elts is not None and date <= x.eol_elts)
        ]
        return distros

    def testing(
        self, date: typing.Optional[datetime.date] = None, result: str = "codename"
    ) -> typing.Union[DistroRelease, str]:
        """Get latest testing Debian distribution based on the given date."""
        if date is None:
            date = self._date
        distros = [
            x
            for x in self._avail(date)
            if (x.release is None and x.version)
            or (x.release is not None and date < x.release and (x.eol is None or date <= x.eol))
        ]
        if not distros:
            raise DistroDataOutdated()
        return self._format(result, distros[-1])

    def valid(self, codename: str) -> bool:
        """Check if the given codename is known."""
        return DistroInfo.valid(self, codename) or codename in [
            "unstable",
            "testing",
            "stable",
            "oldstable",
        ]


class UbuntuDistroInfo(DistroInfo):
    """provides information about Ubuntu's distributions"""

    def __init__(self) -> None:
        super().__init__("Ubuntu")

    def lts(
        self, date: typing.Optional[datetime.date] = None, result: str = "codename"
    ) -> typing.Union[DistroRelease, str]:
        """Get latest long term support (LTS) Ubuntu distribution based on the
        given date."""
        if date is None:
            date = self._date
        distros = [
            x
            for x in self._releases
            if x.version.find("LTS") >= 0 and x.release and x.eol and x.release <= date <= x.eol
        ]
        if not distros:
            raise DistroDataOutdated()
        return self._format(result, distros[-1])

    def is_lts(self, codename: str) -> bool:
        """Is codename an LTS release?"""
        distros = [x for x in self._releases if x.series == codename]
        if not distros:
            return False
        return "LTS" in distros[0].version

    def supported(
        self, date: typing.Optional[datetime.date] = None, result: str = "codename"
    ) -> list[typing.Union[DistroRelease, str]]:
        """Get list of all supported Ubuntu distributions based on the given
        date."""
        if date is None:
            date = self._date
        distros = [
            self._format(result, x)
            for x in self._avail(date)
            if (x.eol and date <= x.eol) or (x.eol_server is not None and date <= x.eol_server)
        ]
        return distros

    def supported_esm(
        self, date: typing.Optional[datetime.date] = None, result: str = "codename"
    ) -> list[typing.Union[DistroRelease, str]]:
        """Get list of all ESM supported Ubuntu distributions based on the
        given date."""
        if date is None:
            date = self._date
        distros = [
            self._format(result, x)
            for x in self._avail(date)
            if x.eol_esm is not None and date <= x.eol_esm
        ]
        return distros
