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


def make_flag_filter(field_name, filter_directive):
    """Make filter function callback to filter out items basing on the provided field and
    directive ("yes", "no", "all")"""
    return lambda item: (
        (filter_directive in ("all", "yes") and item[field_name]) or
        (filter_directive in ("all", "no") and not item[field_name]))


def make_defined_filter(field_name, filter_directive):
    """Make filter function callback to filter out items basing on the provided field (being or not
    being None) and the filter directive ("yes", "no", "all")"""
    return lambda item: (
        (filter_directive in ("all", "yes") and item[field_name] is not None) or
        (filter_directive in ("all", "no") and not item[field_name] is None))
