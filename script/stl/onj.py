def extract_epic_name(item_element):
    for field in item_element.find("customfields").iter("customfield"):
        if field.attrib["id"] == "customfield_10005":
            return field.find("customfieldvalues").find("customfieldvalue").text
    return None


def extract_story_point_number(item_element):
    for field in item_element.find("customfields").iter("customfield"):
        if field.attrib["id"] == "customfield_10024":
            raw = field.find("customfieldvalues").find("customfieldvalue").text
            return int(float(raw))
    return None


def status_to_code(text):
    return {
        "Backlog": "ready",
        "Selected for Development": "ready",
        "In Progress": "work",
        "Done": "done"
    }.get(text, "ready")
    

def priority_to_idx(text):
    return {
        "Critical": 1,
        "Blocker": 1,
        "Highest": 1,
        "High": 2,
        "Medium": 3,
        "Normal": 3,
        "Low": 4,
        "Lowest": 4,
        "Required Optimization": 4
    }.get(text, -2)
