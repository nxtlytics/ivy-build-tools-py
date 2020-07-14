from setuptools import find_packages
from subprocess import check_output, CalledProcessError
from pipfile.api import Pipfile
import toml
from io import open
from typing import *


class IvyBuildTools:
    _pipfile = None
    _package_meta = None

    def __init__(self):
        # Load the Pipfile for use later
        try:
            f = Pipfile.find()
            self._pipfile = toml.load(f)
            self._package_meta = self._pipfile["package"]
        except Exception as e:
            raise FileNotFoundError(
                f"{__class__.__name__} requires a valid Pipfile to generate a setup.py. Cannot continue."
            ) from e

    @property
    def name(self) -> str:
        """
        Get the name of this package
        """
        return self._get_package_meta("name", failure_msg="No package name specified in Pipfile. Cannot continue.")

    @property
    def description(self) -> str:
        """
        Get the short description of this package
        """
        return self._get_package_meta(
            "description", failure_msg="No description specified in Pipfile. Cannot continue."
        )

    @property
    def long_description(self) -> Optional[str]:
        """
        Get the long description of this package
        """
        try:
            with open("README.md", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"[{__class__.__name__}] WARN: Unable to find a README.md to use as package long description.")
            return None

    @property
    def version(self) -> str:
        """
        Get the version of this package
        """
        version_override = self._package_meta.get("version")
        if version_override:
            return version_override
        else:
            try:
                return self.generate_version()
            except Exception as e:
                raise Exception(
                    "Cannot generate package version from git tags. Add some tags or add version to "
                    "Pipfile. Cannot continue."
                ) from e

    @property
    def author(self) -> str:
        """
        Get the author of this package
        """
        return self._get_package_meta("author", failure_msg="No author specified in Pipfile. Cannot continue.")

    @property
    def url(self) -> str:
        """
        Get the Git package URL for this package
        """
        return self._get_package_meta("url", failure_msg="No URL specified in Pipfile. Cannot continue.")

    @property
    def python_requires(self) -> str:
        """
        Get the lowest version of Python supported by this package. Will cap at python 4.x.
        """
        try:
            return f">={self._pipfile['requires']['python_version']}, <4"
        except KeyError as e:
            default = ">=3.7, <4"
            print(
                f"[{__class__.__name__}] WARN: Unable to find required python version for this module, using default [{default}]."
            )

    @property
    def install_requires(self) -> List[str]:
        """
        Get the list of packages required for installation of this package
        """
        return self._generate_requires()

    def _generate_requires(self) -> List[str]:
        """
        Generate the required package list for installation of this package.
        Uses cheat-y logic inspired from pipenv-setup

        TODO: This could potentially be replaced with better code if breaking examples are found.
        """
        pipfile_reqs = self._pipfile["packages"]
        requires: List[str] = []
        for pkg, ver in pipfile_reqs.items():
            # cheat this by setting unpinned versions to empty string
            # potato * => potato
            # potato >1 => potato>1
            if "*" in ver:
                ver = ""
            requires.append(f"{pkg}{ver}")
        return requires

    def _get_package_meta(self, key: str, failure_msg: str, default: str = "", required: bool = True) -> str:
        """
        Get a value from the package metadata dictionary and raise an exception if unable to proceed.
        :param key: Key to return
        :param failure_msg: Message to raise as an Exception if key is nonexistent
        :return: Value of ``package_meta[key]`` if it exists
        """
        try:
            return self._package_meta[key]
        except KeyError as e:
            if required:
                raise Exception(failure_msg) from e
            else:
                print(
                    f"[{__class__.__name__}] WARN: Unable to find [{key}] in Pipfile package section. Continuing anyway "
                    f"with default [{default}]."
                )
                return default

    @staticmethod
    def generate_version(fmt="{tag}{branchcommit}") -> str:
        """
        Generate build version based off of git commit and branch name/hash

        Example:
            initial default/release version: 0.0.1-init
            f1 branch: 0.0.1-f1+1fbcd422 (?)
            merged into develop: 0.0.1-develop+a6cbf891
            merged back into master: 0.0.2
        """
        gitver_command = "git describe --tags --long --dirty"
        gitbranch_command = "git rev-parse --abbrev-ref HEAD"
        try:
            version = check_output(gitver_command.split()).decode("utf-8").strip()
        except CalledProcessError as e:
            raise Exception("No git tags found") from e
        try:
            branch = check_output(gitbranch_command.split()).decode("utf-8").strip()
        except CalledProcessError as e:
            raise Exception("Unable to find git branch name") from e
        parts = version.split("-")
        assert len(parts) in (3, 4), "Cannot parse git tags"
        dirty = len(parts) == 4
        tag, count, sha = parts[:3]
        sha = sha[1:]
        branchcommit = "" if branch == "master" else "-{}-{}".format(branch, sha)
        return fmt.format(
            tag=tag, count=count, sha=sha, dirty=dirty, branch=branch, version=version, branchcommit=branchcommit
        )

    def generate_setup(self) -> Dict[str, Union[str, List[str]]]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "long_description": self.long_description,
            "long_description_content_type": "text/markdown",
            "url": self.url,
            "author": self.author,
            "packages": find_packages(exclude=["contrib", "docs", "tests", "test"]),
            "python_requires": self.python_requires,
            "install_requires": self.install_requires,
        }
