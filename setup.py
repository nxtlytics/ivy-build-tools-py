#!/usr/bin/env python3

from ivybuildtools import IvyBuildTools
from setuptools import setup

# Only run if this is the entry point
if __name__ == "__main__":
    # Generate build arguments.
    setup_args = IvyBuildTools().generate_setup()

    # Override setup arguments like so:
    # setup_args.update(
    #     python_requires="<3.8"
    # )

    # Call setuptools with the standard build arguments
    setup(**setup_args)
