# SPDX-License-Identifier: MIT
# Copyright (C) 2020 Dariusz Walczak <dariusz.walczak@gmail.com>
# Copyright (C) 2020-2021 Mobica Limited

"""Application startup utilities"""

# Standard library imports:
import sys
import traceback

# Project imports:
import cjm.codes


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
        sys.exit(main(options))
    except cjm.codes.CjmError as e:
        if options.verbose:
            traceback.print_exc(file=sys.stderr)
        sys.exit(e.code)


def run_2(main_cb, parse_options_cb, argv=None, defaults=None):
    """
    Alternative wrapper executing provided GEM application entry function. Load defaults if not
    specified, invoke options parsing callback and finally execute the entry funtion.
    """
    defaults = cjm.cfg.load_defaults() if defaults is None else defaults
    argv = sys.argv[1:] if argv is None else argv

    options = parse_options_cb(argv, defaults)

    try:
        sys.exit(main_cb(options, defaults))
    except cjm.codes.CjmError as e:
        if options.verbose:
            traceback.print_exc(file=sys.stderr)
        sys.exit(e.code)
