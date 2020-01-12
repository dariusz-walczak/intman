# Project imports
import cjm.schema

# Third party imports
import jsonschema
import simplejson

# Project imports
import cjm.request


def generate_sprint_name(project_name, start_dt, end_dt):
    _, start_ww, _ = start_dt.isocalendar()
    _, end_ww, _ = end_dt.isocalendar()

    return "{0:s} WW{1:02d}-WW{2:02d}".format(project_name, start_ww, end_ww)


def load_data(cfg, sprint_file):
    schema = cjm.schema.load(cfg, "sprint.json")
    data = simplejson.load(sprint_file)
    jsonschema.validate(data, schema)
    return data


def request_issues_by_sprint(cfg):
    issues = []

    sprint_issues_url = cjm.request.make_cj_agile_url(
        cfg, "sprint/{0:d}/issue".format(cfg["sprint"]["id"]))

    start_at = 0
    max_results = 50

    while True:
        result_code, response = cjm.request.make_cj_request(
            cfg, sprint_issues_url,
            {"startAt": start_at, "maxResults": max_results})

        if result_code:
            return (result_code, issues)

        response_json = response.json()

        for issue in response_json["issues"]:
            issue_data = {
                "id": issue["id"],
                "key": issue["key"],
                "summary": issue["fields"]["summary"]
            }
            issues.append(issue_data)

        start_at += max_results

        if start_at >= response_json["total"]:
            break


    return (cjm.codes.NO_ERROR, issues)
