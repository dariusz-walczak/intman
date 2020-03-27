"""Delivery data processing helpers"""

# Standard library imports
import json

# Third party imports
import jsonschema

# Project imports
import cjm.schema
import cjm.request


def load_data(cfg, delivery_file):
    """Load and validate given delivery data file"""
    schema = cjm.schema.load(cfg, "delivery.json")
    data = json.load(delivery_file)
    jsonschema.validate(data, schema)
    return data
