# SPDX-License-Identifier: MIT
# Copyright (C) 2020-2021 Mobica Limited

"""JSON schema data handling helpers"""

# Standard library imports
import os
import json


def make_subpath(schema_file):
    """Construct a relative schema file path"""
    return os.path.join("cjm", "schema", schema_file)


def load(cfg, name):
    """Load specified JSON schema"""
    schema_path = os.path.join(cfg["path"]["data"], make_subpath(name))
    return json.load(open(schema_path))
