"""General data and data file operations"""

# Standard library imports
import json
import sys

# Third party imports
import jsonschema

# Project imports
import cjm.codes
import cjm.schema


def load(cfg, file_name, schema_name):
    """Load and validate specified json data file. Take care for handling of common file system
       errors"""
    try:
        with open(file_name) as data_file:
            schema = cjm.schema.load(cfg, schema_name)
            data = json.load(data_file)
            jsonschema.validate(data, schema)
    except IOError as e:
        sys.stderr.write(
            "ERROR: Team data file ('{0:s}') I/O error\n".format(file_name))
        sys.stderr.write("    {0}\n".format(e))
        raise cjm.codes.CjmError(cjm.codes.FILESYSTEM_ERROR)

    return data
