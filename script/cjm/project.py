# SPDX-License-Identifier: MIT
# Copyright (C) 2020-2021 Mobica Limited

"""Jira project related helpers"""

# Project imports
import cjm.codes
import cjm.request


def request_project_by_key(cfg, project_key):
    """Request project data by jira project key"""

    url = cjm.request.make_cj_url(cfg, "project", project_key)
    response = cjm.request.make_cj_request(cfg, url)
    return response.json()
