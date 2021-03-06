#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: MIT
# Copyright (C) 2020-2021 Mobica Limited

"""Command line script generating capacity report odt file"""

# Standard library imports
import datetime

# Third party imports
import dateutil.parser
import odf.dc
import odf.draw
import odf.opendocument
import odf.style
import odf.table
import odf.text


# Project imports
import cjm
import cjm.capacity
import cjm.cfg
import cjm.codes
import cjm.commitment
import cjm.data
import cjm.delivery
import cjm.report
import cjm.request
import cjm.run
import cjm.schema
import cjm.sprint
import cjm.team


def parse_options(args, defaults):
    """Parse command line options"""
    parser = cjm.cfg.make_common_parser(defaults)

    cjm.report.add_report_arguments(
        parser.add_argument_group(
            "Report", "Options related to report document generation"),
        "capacity_report.odt",
        defaults)

    return parser.parse_args(args)


def append_head_table(cfg, doc, sprint_data, team_capacity):
    """Add document header table"""

    rows = (
        ("Client", cfg["client"]["name"]),
        ("Project", sprint_data["project"]["name"]),
        ("Sprint Weeks", cjm.report.make_sprint_period_val(cfg)),
        ("Sprint Duration", cjm.report.make_sprint_duration_val(sprint_data)),
        ("Sprint Workdays", cjm.report.make_sprint_workdays_val(team_capacity)),
        ("Report Author", cjm.team.request_user_full_name(cfg)),
        ("Report Date", cjm.report.make_current_date_cell_val_cb()))

    cjm.report.append_head_table(doc, rows)


def append_capacity_table(doc, sprint_data, people):
    """Add personal capacity section"""

    cjm.report.add_elements(
        doc.automaticstyles,
        cjm.report.add_elements(
            odf.style.Style(name="Table.People", family="table"),
            odf.style.TableProperties(width="6.7in", align="margins")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.People.A", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="3.45in")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.People.B", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="1.25in")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.People.C", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="1in")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.People.D", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="1in")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.People.y", family="table-row"),
            odf.style.TableRowProperties(keeptogether="always")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.People.x.1", family="table-cell"),
            cjm.report.make_caption_hor_cell_props()),
        cjm.report.add_elements(
            odf.style.Style(name="Table.People.x.y", family="table-cell"),
            cjm.report.make_value_cell_props()))

    def __make_row(person_idx, person):
        capacity_formula = "<C{0:d}>*{1:d}".format(person_idx+1, person["daily capacity"])

        return cjm.report.add_elements(
            odf.table.TableRow(stylename=doc.getStyleByName("Table.People.y")),
            cjm.report.add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table.People.x.y")),
                odf.text.P(
                    stylename=doc.getStyleByName("Mobica Table Cell"),
                    text="{0:s}, {1:s}".format(person["last name"], person["first name"]))),
            cjm.report.add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table.People.x.y")),
                odf.text.P(
                    stylename=doc.getStyleByName("Mobica Table Cell"),
                    text=sprint_data["project"]["name"])),
            cjm.report.add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table.People.x.y")),
                odf.text.P(
                    stylename=doc.getStyleByName("Mobica Table Cell Right"),
                    text="{0:d}".format(person["sprint workday count"]))),
            cjm.report.add_elements(
                odf.table.TableCell(
                    stylename=doc.getStyleByName("Table.People.x.y"),
                    valuetype="float",
                    formula=capacity_formula),
                odf.text.P(
                    stylename=doc.getStyleByName("Mobica Table Cell Right"))))


    cjm.report.add_elements(
        doc.text,
        odf.text.H(
            outlinelevel=2, stylename=doc.getStyleByName("Mobica Heading 2"),
            text="Personal Capacity"),
        cjm.report.add_elements(
            odf.table.Table(stylename="Table.People"),
            odf.table.TableColumn(stylename="Table.People.A"),
            odf.table.TableColumn(stylename="Table.People.B"),
            odf.table.TableColumn(stylename="Table.People.C"),
            odf.table.TableColumn(stylename="Table.People.D"),
            cjm.report.add_elements(
                odf.table.TableHeaderRows(),
                cjm.report.add_elements(
                    odf.table.TableRow(stylename=doc.getStyleByName("Table.People.y")),
                    cjm.report.add_elements(
                        odf.table.TableCell(stylename=doc.getStyleByName("Table.People.x.1")),
                        odf.text.P(
                            text="Engineer Name",
                            stylename=doc.getStyleByName("Mobica Table Header Left"))),
                    cjm.report.add_elements(
                        odf.table.TableCell(stylename=doc.getStyleByName("Table.People.x.1")),
                        odf.text.P(
                            text="Team",
                            stylename=doc.getStyleByName("Mobica Table Header Left"))),
                    cjm.report.add_elements(
                        odf.table.TableCell(stylename=doc.getStyleByName("Table.People.x.1")),
                        odf.text.P(
                            text="Workdays",
                            stylename=doc.getStyleByName("Mobica Table Header Right"))),
                    cjm.report.add_elements(
                        odf.table.TableCell(stylename=doc.getStyleByName("Table.People.x.1")),
                        odf.text.P(
                            text="SP Capacity",
                            stylename=doc.getStyleByName("Mobica Table Header Right"))))),
            *[__make_row(i, p) for i, p in enumerate(people, 1)],
            cjm.report.add_elements(
                odf.table.TableRow(stylename=doc.getStyleByName("Table.People.y")),
                cjm.report.add_elements(
                    odf.table.TableCell(
                        stylename=doc.getStyleByName("Table.People.x.1"),
                        numbercolumnsspanned="2"),
                    odf.text.P(
                        text="Total:",
                        stylename=doc.getStyleByName("Mobica Table Header Right"))),
                odf.table.CoveredTableCell(),
                cjm.report.add_elements(
                    odf.table.TableCell(
                        stylename=doc.getStyleByName("Table.People.x.1"),
                        valuetype="float",
                        formula="SUM(<C2:C{0:d}>)".format(len(people)+1)),
                    odf.text.P(
                        stylename=doc.getStyleByName("Mobica Table Header Right"))),
                cjm.report.add_elements(
                    odf.table.TableCell(
                        stylename=doc.getStyleByName("Table.People.x.1"),
                        valuetype="float",
                        formula="SUM(<D2:D{0:d}>)".format(len(people)+1)),
                    odf.text.P(
                        stylename=doc.getStyleByName("Mobica Table Header Right"))))))

def create_weekly_table(cfg, doc, week_date, people):
    """Create single week absence table element"""

    monday = cjm.sprint.get_monday(cfg, week_date)

    def __make_person_date_cell(person, date):
        return cjm.report.add_elements(
            odf.table.TableCell(stylename=doc.getStyleByName(
                "Table.Weekly.x.y.r" if date in person["holidays"]
                else "Table.Weekly.x.y.g")),
            odf.text.P(
                text=("???" if date in person["holidays"] else "???"),
                stylename=doc.getStyleByName(
                    "Mobica Table Cell Red" if date in person["holidays"]
                    else "Mobica Table Cell Green")))

    def __make_row(person):
        return cjm.report.add_elements(
            odf.table.TableRow(stylename=doc.getStyleByName("Table.Weekly.y")),
            cjm.report.add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table.Weekly.x.y")),
                odf.text.P(
                    stylename=doc.getStyleByName("Mobica Table Cell"),
                    text="{0:s}, {1:s}".format(person["last name"], person["first name"]))),
            *[__make_person_date_cell(person, monday+datetime.timedelta(days=offset))
              for offset in range(5)])

    return cjm.report.add_elements(
        odf.table.Table(stylename="Table.Weekly"),
        odf.table.TableColumn(stylename="Table.Weekly.A"),
        odf.table.TableColumn(stylename="Table.Weekly.B", numbercolumnsrepeated=5),
        cjm.report.add_elements(
            odf.table.TableHeaderRows(),
            cjm.report.add_elements(
                odf.table.TableRow(stylename=doc.getStyleByName("Table.Weekly.y")),
                cjm.report.add_elements(
                    odf.table.TableCell(stylename=doc.getStyleByName("Table.Weekly.x.1")),
                    odf.text.P(
                        text="Engineer Name",
                        stylename=doc.getStyleByName("Mobica Table Header Left"))),
                cjm.report.add_elements(
                    odf.table.TableCell(stylename=doc.getStyleByName("Table.Weekly.x.1")),
                    odf.text.P(
                        text=monday.strftime("%b %d"),
                        stylename=doc.getStyleByName("Mobica Table Header Left"))),
                cjm.report.add_elements(
                    odf.table.TableCell(stylename=doc.getStyleByName("Table.Weekly.x.1")),
                    odf.text.P(
                        text=(monday + datetime.timedelta(days=1)).strftime("%b %d"),
                        stylename=doc.getStyleByName("Mobica Table Header Left"))),
                cjm.report.add_elements(
                    odf.table.TableCell(stylename=doc.getStyleByName("Table.Weekly.x.1")),
                    odf.text.P(
                        text=(monday + datetime.timedelta(days=2)).strftime("%b %d"),
                        stylename=doc.getStyleByName("Mobica Table Header Left"))),
                cjm.report.add_elements(
                    odf.table.TableCell(stylename=doc.getStyleByName("Table.Weekly.x.1")),
                    odf.text.P(
                        text=(monday + datetime.timedelta(days=3)).strftime("%b %d"),
                        stylename=doc.getStyleByName("Mobica Table Header Left"))),
                cjm.report.add_elements(
                    odf.table.TableCell(stylename=doc.getStyleByName("Table.Weekly.x.1")),
                    odf.text.P(
                        text=(monday + datetime.timedelta(days=4)).strftime("%b %d"),
                        stylename=doc.getStyleByName("Mobica Table Header Left"))))),
        *[__make_row(p) for p in people])


def make_green_cell_props():
    """Create table cell properties object for the absence cells"""

    tcp = odf.style.TableCellProperties()
    tcp.setAttrNS(odf.namespaces.FONS, "background-color", "#bee3d3")
    tcp.setAttrNS(odf.namespaces.FONS, "padding", "0.0382in")
    tcp.setAttrNS(odf.namespaces.FONS, "border", "0.05pt solid #000000")
    return tcp


def make_red_cell_props():
    """Create table cell properties object for the absence cells"""

    tcp = odf.style.TableCellProperties()
    tcp.setAttrNS(odf.namespaces.FONS, "background-color", "#fcd4d1")
    tcp.setAttrNS(odf.namespaces.FONS, "padding", "0.0382in")
    tcp.setAttrNS(odf.namespaces.FONS, "border", "0.05pt solid #000000")
    return tcp


def append_weekly_section(cfg, doc, people):
    """Add weekly absence view section"""

    cjm.report.add_elements(
        doc.automaticstyles,
        cjm.report.add_elements(
            odf.style.Style(name="Table.Weekly", family="table"),
            odf.style.TableProperties(width="6.7in", align="margins")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.Weekly.A", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="2.45in")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.Weekly.B", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="0.85in")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.Weekly.y", family="table-row"),
            odf.style.TableRowProperties(keeptogether="always")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.Weekly.x.1", family="table-cell"),
            cjm.report.make_caption_hor_cell_props()),
        cjm.report.add_elements(
            odf.style.Style(name="Table.Weekly.x.y.g", family="table-cell"),
            make_green_cell_props()),
        cjm.report.add_elements(
            odf.style.Style(name="Table.Weekly.x.y.r", family="table-cell"),
            make_red_cell_props()),
        cjm.report.add_elements(
            odf.style.Style(name="Table.Weekly.x.y", family="table-cell"),
            cjm.report.make_value_cell_props()))

    if cfg["report"]["capacity"]["page break"]["absence section"]:
        section_props = odf.style.ParagraphProperties(breakbefore="page")
    else:
        section_props = odf.style.ParagraphProperties()

    if cfg["report"]["capacity"]["page break"]["weekly table"]:
        separator_props = odf.style.ParagraphProperties(breakbefore="page")
    else:
        separator_props = odf.style.ParagraphProperties()

    cjm.report.add_elements(
        doc.automaticstyles,
        cjm.report.add_elements(
            odf.style.Style(
                name="Section.Absence.Header", family="paragraph",
                parentstylename="Mobica Heading 2"),
            section_props),
        cjm.report.add_elements(
            odf.style.Style(
                name="Section.Absence.Separator", family="paragraph",
                parentstylename="Mobica Default"),
            separator_props))

    cjm.report.add_elements(
        doc.text,
        odf.text.H(
            outlinelevel=2, stylename=doc.getStyleByName("Section.Absence.Header"),
            text="Weekly Absence View"))

    weeks_cnt = ((cfg["sprint"]["end date"] - cfg["sprint"]["start date"]).days + 1) // 7

    cjm.report.join_elements(
        doc.text,
        odf.text.P(text="", stylename=doc.getStyleByName("Section.Absence.Separator")),
        *[create_weekly_table(
            cfg, doc,
            cfg["sprint"]["start date"] + datetime.timedelta(days=7*week_delta),
            people)
          for week_delta in range(weeks_cnt)])


def generate_odt_document(cfg, sprint_data, capacity_data):
    """Main function generating the delivery report document"""
    print("Report template: {0:s}".format(cfg["path"]["report template"]))

    doc = odf.opendocument.load(cfg["path"]["report template"])
    doc.text.childNodes = []

    team_capacity = cjm.capacity.process_team_capacity(sprint_data, capacity_data)
    people = sorted(
        [cjm.capacity.process_person_capacity(team_capacity, p)
         for p in capacity_data["people"]
         if p["daily capacity"] > 0],
        key=lambda p: (p["last name"], p["first name"]))

    cjm.report.append_doc_title(cfg, doc, sprint_data, "Capacity")
    append_head_table(cfg, doc, sprint_data, team_capacity)
    append_capacity_table(doc, sprint_data, people)
    append_weekly_section(cfg, doc, people)

    doc.save(cfg["path"]["output"])

    print("Report saved to: {0:s}".format(cfg["path"]["output"]))


def main(options, defaults):
    """Entry function"""
    cfg = cjm.report.apply_options(
        cjm.cfg.apply_config(cjm.cfg.init_defaults(), defaults), options)

    sprint_data = cjm.data.load(cfg, options.sprint_file, "sprint.json")

    cfg["sprint"]["start date"] = dateutil.parser.parse(sprint_data["start date"]).date()
    cfg["sprint"]["end date"] = dateutil.parser.parse(sprint_data["end date"]).date()

    cjm.sprint.apply_data_file_paths(cfg, sprint_data)

    capacity_data = cjm.data.load(cfg, cfg["path"]["capacity"], "capacity.json")

    generate_odt_document(cfg, sprint_data, capacity_data)

    return cjm.codes.NO_ERROR


if __name__ == "__main__":
    cjm.run.run_2(main, parse_options)
