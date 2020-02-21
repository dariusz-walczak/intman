# Standard library imports
import json

# Third party imports
import jsonschema

# Project imports
import cjm.schema


def load_data(cfg, capacity_file):
    schema = cjm.schema.load(cfg, "capacity.json")
    data = json.load(capacity_file)
    jsonschema.validate(data, schema)
    return data
