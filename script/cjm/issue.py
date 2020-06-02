"""Issue related helper functions"""

# Standard library imports
import copy
import sys

# Project imports
import cjm.codes
import cjm.request


JIRA_COMMENT_CONTENT_TYPE_PARAGRAPH = "paragraph"
JIRA_COMMENT_CONTENT_TYPE_TEXT = "text"



def assigned_issues(issues):
    """Extract list of issues assigned to anyone"""
    return [
        copy.copy(i) for i in issues
        if i["assignee id"] is not None]


def unassigned_issues(issues):
    """Extract list of unassigned issues"""
    return [
        copy.copy(i) for i in issues
        if i["assignee id"] is None]


def person_issues(issues, person_data):
    """Extract list of issues assigned to the given person"""
    return [
        copy.copy(i) for i in issues
        if i["assignee id"] == person_data["account id"]]


def detect_story_point_field_id(cfg):
    """Determine identifier of the story point issue field"""
    url = cjm.request.make_cj_url(cfg, "field")
    response = cjm.request.make_cj_request(cfg, url)

    for field in response.json():
        if field["name"] == "Story Points":
            return field["id"]

    raise cjm.codes.CjmError(cjm.codes.INTEGRATION_ERROR)


def detect_epic_link_field_id(cfg):
    """Determine identifier of the epic link issue field"""
    url = cjm.request.make_cj_url(cfg, "field")
    response = cjm.request.make_cj_request(cfg, url)

    for field in response.json():
        if field["name"] == "Epic Link":
            return field["id"]

    raise cjm.codes.CjmError(cjm.codes.INTEGRATION_ERROR)


def detect_epic_name_field_id(cfg):
    """Determine identifier of the epic name issue field"""
    url = cjm.request.make_cj_url(cfg, "field")
    response = cjm.request.make_cj_request(cfg, url)

    for field in response.json():
        if field["name"] == "Epic Name":
            return field["id"]

    raise cjm.codes.CjmError(cjm.codes.INTEGRATION_ERROR)


EPIC_COLORS = {
    "black": "ghx-label-1",
    "dark-yellow": "ghx-label-2",
    "light-yellow": "ghx-label-3",
    "dark-blue": "ghx-label-4",
    "dark-aqua": "ghx-label-5",
    "light-green": "ghx-label-6",
    "light-purple": "ghx-label-7",
    "dark-purple": "ghx-label-8",
    "light-pink": "ghx-label-9",
    "light-blue": "ghx-label-10",
    "light-aqua": "ghx-label-11",
    "light-gray": "ghx-label-12",
    "dark-green": "ghx-label-13",
    "dark-red": "ghx-label-14"
}


def request_epic_update(cfg, issue_spec):
    """Update epic name and optionally color"""
    epic_name = issue_spec["epic"]["name"]
    epic_color = issue_spec["epic"].get("color")

    json = {
        "name": epic_name
    }

    if epic_color is not None:
        json["color"]: {
            "key": EPIC_COLORS[epic_color]
        }

    url = cjm.request.make_cj_agile_url(cfg, "epic", issue_spec["key"])
    cjm.request.make_cj_post_request(cfg, url, json=json)


def request_issue_comments_regexp(cfg, issue_key, comment_re):
    """Return these of specific issue's comments that match given regular expression"""
    comments = []
    comments_url = cjm.request.make_cj_url(cfg, "issue", issue_key, "comment")

    start_at = 0
    max_results = 50

    while True:
        response = cjm.request.make_cj_request(
            cfg, comments_url,
            params={"startAt": start_at, "maxResults": max_results})
        response_json = response.json()

        for comment in response_json["comments"]:
            for content_l1 in comment["body"]["content"]:
                if content_l1["type"] == JIRA_COMMENT_CONTENT_TYPE_PARAGRAPH:
                    for content_l2 in content_l1["content"]:
                        if content_l2["type"] == JIRA_COMMENT_CONTENT_TYPE_TEXT:
                            m = comment_re.match(content_l2["text"])
                            if m is not None:
                                comments.append(m)

        start_at += max_results

        if start_at >= response_json["total"]:
            break

    return comments


def extract_issue_data(cfg, issue):
    """Common function converting jira issue description to a tailored set of properties"""
    def __account_id_cb(usr):
        return None if usr is None else usr["accountId"]

    return {
        "id": int(issue["id"]),
        "key": issue["key"],
        "summary": issue["fields"]["summary"],
        "assignee id": __account_id_cb(issue["fields"]["assignee"]),
        "story points": issue["fields"].get(cfg["jira"]["fields"]["story points"]),
        "status": issue["fields"]["status"]["name"],
        "resolution date": issue["fields"]["resolutiondate"]
    }


def request_issue(cfg, issue_key):
    """Return issue identified by given key.
    Return None if not found"""
    issue_url = cjm.request.make_cj_url(cfg, "issue", issue_key)
    response = cjm.request.make_cj_request(cfg, issue_url, tolerate_404=True)

    if response.status_code == 404:
        return None
    elif response.status_code != 200:
        sys.stderr.write(
            "ERROR: The Jira API request ('{0:s}') failed with code {1:d}\n"
            "".format(issue_url, response.status_code))
        raise cjm.codes.CjmError(cjm.codes.REQUEST_ERROR)
    response_json = response.json()
    return extract_issue_data(cfg, response_json)


def request_issues_by_keys(cfg, issue_keys):
    """Return issues identified by one of given keys"""
    if not issue_keys:
        return []

    issues = []
    issues_url = cjm.request.make_cj_url(cfg, "search")

    jql = 'key in ({0:s})'.format(", ".join(issue_keys))
    start_at = 0
    max_results = 50

    while True:
        response = cjm.request.make_cj_post_request(
            cfg, issues_url,
            json={"jql": jql, "startAt": start_at, "maxResults": max_results})
        response_json = response.json()

        for issue in response_json["issues"]:
            issues.append(extract_issue_data(cfg, issue))

        start_at += max_results

        if start_at >= response_json["total"]:
            break

    return issues


def make_comment_body(comment_text):
    """Build body of the add issue comment request"""
    return {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "text": comment_text,
                            "type": "text"
                        }
                    ]
                }
            ]
        }
    }


def request_comment_create(cfg, issue_key, comment_json):
    """Request addition of specified comment body to given issue
    The comment body is constructed e.g. by the make_comment_body function"""
    url = cjm.request.make_cj_url(cfg, "issue", issue_key, "comment")
    return cjm.request.make_cj_post_request(cfg, url, json=comment_json).json()


def request_issue_types(cfg):
    """Return issue type list"""
    url = cjm.request.make_cj_url(cfg, "issuetype")
    return cjm.request.make_cj_request(cfg, url).json()


def request_issue_link_types(cfg):
    """Return issue link type list"""
    url = cjm.request.make_cj_url(cfg, "issueLinkType")
    return cjm.request.make_cj_request(cfg, url).json()["issueLinkTypes"]


def request_issue_create(cfg, issue_spec):
    """Post issue creation request"""
    json = {
        "update": {},
        "fields": {
            "summary": issue_spec["title"],
            "issuetype": {
                "id": issue_spec["type id"],
            },
            "project": {
                "id": issue_spec["project id"],
            },
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "text": issue_spec["summary"],
                                "type": "text"
                            }
                        ]
                    }
                ]
            }
        }
    }

    if issue_spec.get("type name") == cfg["jira"]["issue"]["type"]["epic"]:
        json["fields"][cfg["jira"]["fields"]["epic name"]] = issue_spec["epic"]["name"]
    else:
        epic_key = issue_spec.get("epic").get("link", {}).get("key")
        if epic_key is not None:
            json["fields"][cfg["jira"]["fields"]["epic link"]] = epic_key

    create_url = cjm.request.make_cj_url(cfg, "issue")
    response = cjm.request.make_cj_post_request(cfg, create_url, json=json)
    return request_issue(cfg, response.json()["key"])


def request_issue_link_create(cfg, inward_key, outward_key, link_type):
    """Post issue link"""
    json = {
        "inwardIssue": {
            "key": inward_key
        },
        "outwardIssue": {
            "key": outward_key
        },
        "type": {
            "name": link_type
        }
    }

    url = cjm.request.make_cj_url(cfg, "issueLink")
    cjm.request.make_cj_post_request(cfg, url, json=json)
