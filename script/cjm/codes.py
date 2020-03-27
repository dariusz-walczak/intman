"""Provide error handling helpers"""

NO_ERROR = 0
CONFIGURATION_ERROR = 1
REQUEST_ERROR = 2
FILESYSTEM_ERROR = 3
INTEGRATION_ERROR = 4 # Indicates that some assumption about how the Jira works seems to be false
INVALID_ARGUMENT_ERROR = 5

class CjmError(Exception):
    """Exception to be raised by cjm library functions and by cjm-* and sm-* scripts"""
    def __init__(self, code):
        super().__init__(code)
        self.code = code
