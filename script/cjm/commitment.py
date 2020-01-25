# Standard library imports
import json

# Third party imports
import jsonschema

# Project imports
import cjm.schema
import cjm.request


def load_data(cfg, commitment_file):
    schema = cjm.schema.load(cfg, "commitment.json")
    data = json.load(commitment_file)
    jsonschema.validate(data, schema)
    return data
