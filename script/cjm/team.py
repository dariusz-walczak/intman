# Standard library imports
import json

# Third party imports
import jsonschema

# Project imports
import cjm.schema
import cjm.request


def load_data(cfg, team_file):
    schema = cjm.schema.load(cfg, "team.json")
    data = json.load(team_file)
    jsonschema.validate(data, schema)
    return data
