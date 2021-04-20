# Copyright © 2020 by Dariusz Walczak
# Copyright © 2020-2021 Mobica Limited

"""Application startup utilities

Parts of this file are subject of following license and copyright:
---------------------------------------------------------------------------------------------------
Copyright (C) 2020 by Dariusz Walczak

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT
OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
---------------------------------------------------------------------------------------------------

Parts of this file are subject of following copyright:
---------------------------------------------------------------------------------------------------
Copyright © 2020-2021 Mobica Limited. All rights reserved.
"""

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
