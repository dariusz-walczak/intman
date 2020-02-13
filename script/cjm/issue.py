# Project imports
import cjm.codes
import cjm.request


JIRA_COMMENT_CONTENT_TYPE_PARAGRAPH = "paragraph"
JIRA_COMMENT_CONTENT_TYPE_TEXT = "text"


def detect_story_point_field_id(cfg):
    url = cjm.request.make_cj_url(cfg, "field")
    result_code, response = cjm.request.make_cj_request(cfg, url)

    if result_code:
        return result_code, None

    for field in response.json():
        if field["name"] == "Story Points":
            return cjm.codes.NO_ERROR, field["id"]

    return cjm.codes.INTEGRATION_ERROR, None


def request_issue_comments_by_regexp(cfg, issue_key, comment_re):
    comments = []
    comments_url = cjm.request.make_cj_url(cfg, "issue", issue_key, "comment")

    start_at = 0
    max_results = 50

    while True:
        result_code, response = cjm.request.make_cj_request(
            cfg, comments_url,
            params={"startAt": start_at, "maxResults": max_results})

        if result_code:
            return result_code, comments

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
    def __account_id_cb(u):
        return None if u is None else u["accountId"]

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
    if not issue_keys:
        return cjm.codes.NO_ERROR, []

    issues = []
    issues_url = cjm.request.make_cj_url(cfg, "search".format(cfg["sprint"]["id"]))

    jql = 'key in ({0:s})'.format(", ".join(issue_keys))
    start_at = 0
    max_results = 50

    while True:
        result_code, response = cjm.request.make_cj_post_request(
            cfg, issues_url,
            json={"jql": jql, "startAt": start_at, "maxResults": max_results})

        if result_code:
            return result_code, issues

        response_json = response.json()

        for issue in response_json["issues"]:
            issues.append(extract_issue_data(cfg, issue))

        start_at += max_results

        if start_at >= response_json["total"]:
            break

    return cjm.codes.NO_ERROR, issues
