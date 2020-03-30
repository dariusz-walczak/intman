"""Issue related helper functions"""

# Standard library imports
import copy

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

    return cjm.codes.NO_ERROR, comments


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


def request_issues_by_keys(cfg, issue_keys):
    """Return issues identified by one of given keys"""
    if not issue_keys:
        return cjm.codes.NO_ERROR, []

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

    return cjm.codes.NO_ERROR, issues


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
