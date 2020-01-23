# Standard library imports
import os
import json


def make_subpath(schema_file):
    return os.path.join("cjm", "schema", schema_file)


def load(cfg, name):
    schema_path = os.path.join(cfg["path"]["data"], make_subpath(name))
    return json.load(open(schema_path))
