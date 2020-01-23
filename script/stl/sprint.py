import stl.data


def priority_code(priority_index):
    assert priority_index in (-1, -2) or priority_index > 0

    if priority_index in (-1, -2):
        return ""
    else:
        return "P{0:d}".format(priority_index)


def ticket_generate(ticket_data):
    return {
        "task id": ticket_data["id"],
        "task name": ticket_data["name"],
        "sp": ticket_data["sp"],
        "priority": priority_code(ticket_data["priority index"]),
        "status": ticket_data["status"]
    }


def participant_generate(project_member, ticket_data):
    return {
        "commitment": [
            ticket_generate(ticket)
            for ticket in ticket_data
            if ticket["assignee code"] == project_member["code"]
        ],
        "extension": [],
        "code": project_member["code"],
        "name": stl.data.person_full_name(project_member)
    }


def unassigned_generate(ticket_data):
    return [{
        "commitment": [
            ticket_generate(ticket)
            for ticket in ticket_data
            if ticket["assignee code"] is None
        ],
        "extension": [],
        "code": "NONE",
        "name": "Unassigned"
    }]


def team_generate(project_data, ticket_data):
    return {
        "code": project_data["project"]["code"],
        "name": project_data["project"]["name"],
        "people": [
                      participant_generate(project_member, ticket_data)
                      for project_member in project_data["members"]
                  ] + unassigned_generate(ticket_data)
        # "unassigned": [
        #     ticket_generate(ticket)
        #     for ticket in ticket_data
        #     if ticket["assignee code"] is None
        # ]
    }


def plan_generate(team_data, sprint_data, ticket_data):
    wwf = sprint_data.get("ww_first")
    wwl = sprint_data.get("ww_last")

    if wwf is not None:
        if wwl is not None:
            sprint_name = "WW{0:02d}-WW{1:02d}".format(wwf, wwl)
        else:
            sprint_name = "WW{0:02d}".format(wwf)
    else:
        sprint_name = "UNNAMED SPRINT"

    project_list = [
        {
            "project": project,
            "members": members
        }
        for project, members in
        [
            (project, stl.data.project_member_list(team_data, project["code"]))
            for project in team_data["projects"]
        ]
        if members
    ]

    participant_list = [
        person
        for person in team_data["people"]
        if person.get("projects", [])
    ]

    return {
        "capacity": dict(
            (stl.data.person_full_name(person), 20)
            for person in participant_list),
        "jira_list": [],
        "sprint": sprint_name,
        "teams": [
            team_generate(project_data, ticket_data)
            for project_data in project_list
        ]
    }
