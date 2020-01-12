# Standard library imports
import os

# Third party imports
import simplejson


def make_subpath(schema_file):
    return os.path.join("cjm", "schema", schema_file)


def load(cfg, name):
    schema_path = os.path.join(cfg["path"]["data"], make_subpath(name))
    return simplejson.load(open(schema_path))
