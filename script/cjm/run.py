"""Application startup utilities

This is MIT licensed contribution. Copyright (C) 2020 by Dariusz Walczak
"""

# Standard library imports:
import sys
import traceback

# Project imports:
import gem.error


def run(main, options):
    """Wrapper executing provided GEM application entry function

    :param main: Entry function
    :param options: Result of command line arguments parsing (as returned by
    argparse.parser.parse); It is passed directly to the entry function

    The purpose of this function is to invoke provided entry function and use its return value as
    application's exit code. It takes care for ending the application with proper exit code when
    a GEM exception occurs
    """
    try:
        sys.exit(main(options).value)
    except gem.error.GemError as e:
        if options.verbose:
            traceback.print_exc(file=sys.stderr)
        sys.exit(e.code.value)
