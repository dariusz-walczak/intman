# Standard imports
import json

# Third party imports
import jsonschema

# Project imports
import cjm.issue
import cjm.schema
import cjm.request
import cjm.codes


def generate_sprint_name(project_name, start_dt, end_dt):
    _, start_ww, _ = start_dt.isocalendar()
    _, end_ww, _ = end_dt.isocalendar()

    if start_ww != end_ww:
        return "{0:s} WW{1:02d}-WW{2:02d}".format(project_name, start_ww, end_ww)
    else:
        return "{0:s} WW{1:02d}".format(project_name, start_ww)


def load_data(cfg, sprint_file):
    schema = cjm.schema.load(cfg, "sprint.json")
    data = json.load(sprint_file)
    jsonschema.validate(data, schema)
    return data


def request_issues_by_sprint(cfg):
    issues = []

    sprint_issues_url = cjm.request.make_cj_agile_url(
        cfg, "sprint/{0:d}/issue".format(cfg["sprint"]["id"]))

    start_at = 0
    max_results = 50

    while True:
        response = cjm.request.make_cj_request(
            cfg, sprint_issues_url,
            {"startAt": start_at, "maxResults": max_results})
        response_json = response.json()

        for issue in response_json["issues"]:
            issues.append(cjm.issue.extract_issue_data(cfg, issue))

        start_at += max_results

        if start_at >= response_json["total"]:
            break

    return cjm.codes.NO_ERROR, issues


def request_issues_by_comment(cfg, comment):
    issues = []

    sprint_issues_url = cjm.request.make_cj_url(cfg, "search".format(cfg["sprint"]["id"]))

    jql = 'project = "{0:s}" AND comment ~ "{1:s}"'.format(cfg["project"]["key"], comment)
    start_at = 0
    max_results = 50

    while True:
        response = cjm.request.make_cj_post_request(
            cfg, sprint_issues_url,
            json={"jql": jql, "startAt": start_at, "maxResults": max_results})
        response_json = response.json()

        for issue in response_json["issues"]:
            issues.append(cjm.issue.extract_issue_data(cfg, issue))

        start_at += max_results

        if start_at >= response_json["total"]:
            break

    return issues
