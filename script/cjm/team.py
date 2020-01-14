# Project imports
import cjm.schema

# Third party imports
import jsonschema
import simplejson

# Project imports
import cjm.schema
import cjm.request



def load_data(cfg, team_file):
    schema = cjm.schema.load(cfg, "team.json")
    data = simplejson.load(team_file)
    jsonschema.validate(data, schema)
    return data
