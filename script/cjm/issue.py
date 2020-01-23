# Project imports
import cjm.codes
import cjm.request


def detect_story_point_field_id(cfg):
    url = cjm.request.make_cj_url(cfg, "field")
    result_code, response = cjm.request.make_cj_request(cfg, url)

    if result_code:
        return result_code, None

    for field in response.json():
        if field["name"] == "Story Points":
            return cjm.codes.NO_ERROR, field["id"]

    return cjm.codes.INTEGRATION_ERROR, None
