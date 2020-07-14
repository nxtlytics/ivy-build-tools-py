from subprocess import check_output
from ivybuildtools import *


def test_name():
    """Ensure name matches"""
    assert IvyBuildTools().name == "ivybuildtools"


def test_version():
    gitver = check_output("git describe --tags".split(" ")).decode("utf-8").strip().split("-")[0]

    bt = IvyBuildTools()

    # ensure IvyBuildTools generates versions containing the branch and tag information correctly
    # (with a simple contains check...)
    assert gitver in bt.version
