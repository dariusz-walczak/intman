# Standard library imports
import os

# Third party imports
import jsonschema
import simplejson


#def epic_list_load(cfg):
#    schema = schema_load(cfg, "epic_list.json


def schema_load(cfg, name):
    return simplejson.load(open(os.path.join(cfg["stl_data_path"], "schema", name)))


def team_data_load(cfg):
    schema = schema_load(cfg, "team_data.json")
    data = simplejson.load(open(os.path.join(cfg["sow_data_path"], "team_data.json")))
    jsonschema.validate(data, schema)
    return data


def account_map_create(team_data, system_code):
    return dict(
        (account["user name"], person)
        for person in team_data["people"]
        for account in person.get("accounts", [])
        if system_code == account["system code"])


def project_member_list(team_data, project_code):
    return [
        person
        for person in team_data["people"]
        if project_code in person["projects"]]


def person_full_name(person):
    return u"{0:s}, {1:s}".format(person["last name"], person["first name"])


def sprint_data_init():
    return {
        "ww_first": None,
        "ww_last": None
    }
