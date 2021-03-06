#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: MIT
# Copyright (C) 2020-2021 Mobica Limited

"""Command line script generating commitment report odt file"""

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
        "commitment_report.odt",
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


def append_summary_section(doc, capacity_data, team_capacity, commitment_data):
    """Add commitment summary section"""

    committed_text = (
        "The total number of committed story points is {0:d}."
        "".format(commitment_data["total"]["committed"]))
    capacity_text = (
        "The sprint capacity is {0:d} story points."
        "".format(_calc_team_capacity(capacity_data, team_capacity)))

    cjm.report.add_elements(
        doc.text,
        odf.text.H(
            outlinelevel=2, stylename=doc.getStyleByName("Mobica Heading 2"),
            text="Summary"),
        cjm.report.add_elements(
            odf.text.List(stylename="L1"),
            cjm.report.add_elements(
                odf.text.ListItem(),
                odf.text.P(
                    stylename=doc.getStyleByName("Mobica Important"),
                    text=committed_text)),
            cjm.report.add_elements(
                odf.text.ListItem(),
                odf.text.P(
                    stylename=doc.getStyleByName("Mobica Default"),
                    text=capacity_text))))


def append_tasks_section(cfg, doc, commitment_data):
    """Add commitment tasks table section"""

    cjm.report.add_elements(
        doc.automaticstyles,
        cjm.report.add_elements(
            odf.style.Style(name="Table.Issues", family="table"),
            odf.style.TableProperties(width="6.7in", align="margins")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.Issues.A", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="1in")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.Issues.B", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="4.6in")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.Issues.C", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="1.1in")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.Issues.y", family="table-row"),
            odf.style.TableRowProperties(keeptogether="always")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.Issues.x.1", family="table-cell"),
            cjm.report.make_caption_hor_cell_props()),
        cjm.report.add_elements(
            odf.style.Style(name="Table.Issues.x.y", family="table-cell"),
            cjm.report.make_value_cell_props()))

    def __make_row(issue):
        return cjm.report.add_elements(
            odf.table.TableRow(stylename=doc.getStyleByName("Table.Issues.y")),
            cjm.report.add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.y")),
                cjm.report.add_elements(
                    odf.text.P(stylename=doc.getStyleByName("Mobica Table Cell")),
                    cjm.report.create_issue_anchor_element(cfg, doc, issue["key"]))),
            cjm.report.add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.y")),
                odf.text.P(
                    stylename=doc.getStyleByName("Mobica Table Cell"),
                    text=issue["summary"])),
            cjm.report.add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.y")),
                odf.text.P(
                    stylename=doc.getStyleByName("Mobica Table Cell Right"),
                    text=issue["story points"])))

    cjm.report.add_elements(
        doc.text,
        odf.text.H(
            outlinelevel=2, stylename=doc.getStyleByName("Mobica Heading 2"),
            text="Committed Task List"),
        cjm.report.add_elements(
            odf.table.Table(stylename="Table.Issues"),
            odf.table.TableColumn(stylename="Table.Issues.A"),
            odf.table.TableColumn(stylename="Table.Issues.B"),
            odf.table.TableColumn(stylename="Table.Issues.C"),
            cjm.report.add_elements(
                odf.table.TableHeaderRows(),
                cjm.report.add_elements(
                    odf.table.TableRow(stylename=doc.getStyleByName("Table.Issues.y")),
                    cjm.report.add_elements(
                        odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.1")),
                        odf.text.P(
                            text="Task Id",
                            stylename=doc.getStyleByName("Mobica Table Header Left"))),
                    cjm.report.add_elements(
                        odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.1")),
                        odf.text.P(
                            text="Task Title",
                            stylename=doc.getStyleByName("Mobica Table Header Left"))),
                    cjm.report.add_elements(
                        odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.1")),
                        odf.text.P(
                            text="Story Points",
                            stylename=doc.getStyleByName("Mobica Table Header Right"))))),
            *[__make_row(issue) for issue in commitment_data["issues"]],
            cjm.report.add_elements(
                odf.table.TableRow(stylename=doc.getStyleByName("Table.Issues.y")),
                cjm.report.add_elements(
                    odf.table.TableCell(
                        stylename=doc.getStyleByName("Table.Issues.x.1"),
                        numbercolumnsspanned="2"),
                    odf.text.P(
                        text="Total:",
                        stylename=doc.getStyleByName("Mobica Table Header Right"))),
                odf.table.CoveredTableCell(),
                cjm.report.add_elements(
                    odf.table.TableCell(
                        stylename=doc.getStyleByName("Table.Issues.x.1"),
                        valuetype="float",
                        formula="SUM(<C2:C{0:d}>)".format(len(commitment_data["issues"])+1)),
                    odf.text.P(
                        stylename=doc.getStyleByName("Mobica Table Header Right"))))))


def generate_odt_document(cfg, capacity_data, commitment_data, sprint_data):
    """Main function generating the commitment report document"""
    print("Report template: {0:s}".format(cfg["path"]["report template"]))

    doc = odf.opendocument.load(cfg["path"]["report template"])
    doc.text.childNodes = []

    team_capacity = cjm.capacity.process_team_capacity(sprint_data, capacity_data)

    cjm.report.append_doc_title(cfg, doc, sprint_data, "Commitment")
    append_head_table(cfg, doc, sprint_data, team_capacity)
    append_summary_section(doc, capacity_data, team_capacity, commitment_data)
    append_tasks_section(cfg, doc, commitment_data)

    doc.save(cfg["path"]["output"])

    print("Report saved to: {0:s}".format(cfg["path"]["output"]))


def _calc_team_capacity(capacity_data, team_capacity):
    return sum(
        cjm.capacity.process_person_capacity(team_capacity, p)["sprint capacity"]
        for p in capacity_data["people"])


def main(options, defaults):
    """Entry function"""
    cfg = cjm.report.apply_options(
        cjm.cfg.apply_config(cjm.cfg.init_defaults(), defaults), options)

    sprint_data = cjm.data.load(cfg, options.sprint_file, "sprint.json")

    cfg["sprint"]["start date"] = dateutil.parser.parse(sprint_data["start date"]).date()
    cfg["sprint"]["end date"] = dateutil.parser.parse(sprint_data["end date"]).date()

    cjm.sprint.apply_data_file_paths(cfg, sprint_data)

    capacity_data = cjm.data.load(cfg, cfg["path"]["capacity"], "capacity.json")
    commitment_data = cjm.data.load(cfg, cfg["path"]["commitment"], "commitment.json")

    generate_odt_document(cfg, capacity_data, commitment_data, sprint_data)

    return cjm.codes.NO_ERROR


if __name__ == "__main__":
    cjm.run.run_2(main, parse_options)
