"""Send reports about subiquity to the correct Launchpad project."""

import os

from apport import hookutils


def add_info(report, unused_ui):
    """Send reports about subiquity to the correct Launchpad project."""
    # TODO: read the version from the log file?
    logfile = os.path.realpath("/var/log/installer/subiquity-debug.log")
    revision = "unknown"
    if os.path.exists(logfile):
        hookutils.attach_file(report, "logfile", "InstallerLog")
        with open(logfile, encoding="utf-8") as log_fp:
            first_line = log_fp.readline()
        marker = "Starting Subiquity revision"
        if marker in first_line:
            revision = first_line.split(marker)[1].strip()
    report["Package"] = f"subiquity ({revision})"
    report["SourcePackage"] = "subiquity"
    # rewrite this section so the report goes to the project in Launchpad
    report[
        "CrashDB"
    ] = """\
{
    "impl": "launchpad",
    "project": "subiquity",
    "bug_pattern_url": "http://people.canonical.com/"
    "~ubuntu-archive/bugpatterns/bugpatterns.xml",
}
"""

    # add in subiquity stuff
    hookutils.attach_file_if_exists(
        report, "/var/log/installer/subiquity-curtin-install.conf", "CurtinConfig"
    )
    hookutils.attach_file_if_exists(
        report, "/var/log/installer/curtin-install.log", "CurtinLog"
    )
    hookutils.attach_file_if_exists(
        report, "/var/log/installer/block/probe-data.json", "ProbeData"
    )

    # collect desktop installer details if available
    desktoplog = os.path.realpath("/var/log/installer/ubuntu_bootstrap.log")
    if os.path.exists(desktoplog):
        hookutils.attach_file(report, desktoplog, "DesktopInstallerLog")
        report.add_tags(["ubuntu-desktop-bootstrap"])
        snapdir = os.path.realpath("/snap/ubuntu-desktop-bootstrap/current")
        if os.path.exists(snapdir):
            report["DesktopInstallerRev"] = os.path.basename(snapdir)
