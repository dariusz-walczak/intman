# SPDX-License-Identifier: MIT
# Copyright (C) 2020-2021 Mobica Limited

"""Provide error handling helpers"""

NO_ERROR = 0
CONFIGURATION_ERROR = 1
REQUEST_ERROR = 2
FILESYSTEM_ERROR = 3
INTEGRATION_ERROR = 4 # Indicates that some assumption about how the Jira works seems to be false
INVALID_ARGUMENT_ERROR = 5
INPUT_DATA_ERROR = 6 # There is some problem with input data
JIRA_DATA_ERROR = 7 # There is some problem with the jira stored data


class CjmError(Exception):
    """Exception to be raised by cjm library functions and by cjm-* and sm-* scripts"""
    def __init__(self, code):
        super().__init__(code)
        self.code = code
