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
        }
    }


def apply_options(cfg, options):
    cfg = copy.copy(cfg)
    cfg["jira"]["user"]["name"] = options.user_name
    cfg["jira"]["user"]["token"] = options.user_token
    return cfg


def apply_options(cfg, options):
    cfg["jira"]["user"]["name"] = options.user_name
    cfg["jira"]["user"]["token"] = options.user_token


cfg = cjm.cfg.init_default()
cjm.cfg.apply_options(cfg, options)

cfg = cjm.cfg.apply_options(cjm.cfg.init_default(), options)
