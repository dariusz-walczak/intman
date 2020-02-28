# Standard library imports
import json

# Third party imports
import jsonschema

# Project imports
import cjm.codes
import cjm.schema


def load(cfg, file_name, schema_name):
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
