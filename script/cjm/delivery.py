# Standard library imports
import json

# Third party imports
import jsonschema

# Project imports
import cjm.schema
import cjm.request


def load_data(cfg, delivery_file):
    schema = cjm.schema.load(cfg, "delivery.json")
    data = json.load(delivery_file)
    jsonschema.validate(data, schema)
    return data
