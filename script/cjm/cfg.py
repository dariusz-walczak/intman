# Standard library:
import copy


def init_default():
    return {
        "jira": {
            "scheme": "https",
            "host":   "openness.atlassian.net",
            "user": {
                "name": None,
                "token": None
            }
        },
        "sprint": {
            "id": None
        },
        "board": {
            "id": None
        },
        "project": {
            "key": None
        },
        "path": {
            "data": None
        }
    }


def apply_options(cfg, options):
    cfg = copy.copy(cfg)
    cfg["jira"]["user"]["name"] = options.user_name
    cfg["jira"]["user"]["token"] = options.user_token
    cfg["path"]["data"] = options.data_dir_path
    return cfg
