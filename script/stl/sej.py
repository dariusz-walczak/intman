def extract_epic_name(item_element):
    for field in item_element.find("customfields").iter("customfield"):
        if field.attrib["id"] == "customfield_10005":
            return field.find("customfieldvalues").find("customfieldvalue").text
    return None


def extract_story_point_number(item_element):
    for field in item_element.find("customfields").iter("customfield"):
        if field.attrib["id"] == "customfield_10002":
            raw = field.find("customfieldvalues").find("customfieldvalue").text
            return int(float(raw))
    return None


def priority_to_idx(text):
    return {
        "Normal": 3
    }.get(text, -2)
