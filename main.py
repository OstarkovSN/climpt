#!/usr/bin/env python3
"""
Climpt - Clipboard Prompt Manager
Entry point for the application
"""

import sys
import logging
import click
from app import ClimptApp

logger = logging.getLogger(__name__)


@click.option("--verbose", "-v", count=True, help="Increase verbosity of logging")
@click.option("--quiet", "-q", count=True, help="Decrease verbosity of logging")
@click.command()
def main(verbose, quiet):
    """Main entry point"""
    verbosity = verbose - quiet + 2
    logging.basicConfig(
        level=max(
            (min(logging.CRITICAL - verbosity * 10, logging.CRITICAL), logging.DEBUG)
        ),
        format="[%(asctime)s] [%(filename)16s:%(lineno)3s)] [%(levelname)8s]: [%(message)s]",
        datefmt="%Y-%m-%d] [%H:%M:%S",
    )
    app = ClimptApp()
    app.MainLoop()
    sys.exit(0)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
