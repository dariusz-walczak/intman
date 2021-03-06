#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: MIT
# Copyright (C) 2020-2021 Mobica Limited

"""Command line script generating delivery report odt file"""

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
        "delivery_report.odt",
        defaults)

    return parser.parse_args(args)


def append_head_table(cfg, doc, sprint_data, delivery_summary, team_capacity):
    """Add document header table"""

    def __delivery_ratio_cell_val_cb(doc):
        part1 = "{0:d}/{1:d} (".format(
            delivery_summary["delivery"], delivery_summary["commitment"])
        part2 = "{0:f}%".format(delivery_summary["delivery ratio"])
        part3 = ")"

        return cjm.report.add_elements(
            odf.text.P(stylename=doc.getStyleByName("Mobica Table Cell")),
            odf.text.Span(text=part1),
            odf.text.Span(text=part2, stylename=doc.getStyleByName("Strong Emphasis")),
            odf.text.Span(text=part3))

    rows = (
        ("Client", cfg["client"]["name"]),
        ("Project", sprint_data["project"]["name"]),
        ("Sprint Weeks", cjm.report.make_sprint_period_val(cfg)),
        ("Sprint Duration", cjm.report.make_sprint_duration_val(sprint_data)),
        ("Sprint Workdays", cjm.report.make_sprint_workdays_val(team_capacity)),
        ("Delivery Ratio", __delivery_ratio_cell_val_cb),
        ("Report Author", cjm.team.request_user_full_name(cfg)),
        ("Report Date", cjm.report.make_current_date_cell_val_cb()))

    cjm.report.append_head_table(doc, rows)


def append_summary_section(doc, commitment_data, delivery_summary):
    """Add delivery summary section"""

    committed_originally_text = (
        "The total number of story points originally committed was {0:d}."
        "".format(commitment_data["total"]["committed"]))
    committed_final_text_1 = (
        "The number of story points taken for delivery ratio calculation was {0:d}"
        "".format(delivery_summary["commitment"]))
    committed_final_text_2 = (
        " (the result of all the drops and extensions).")
    delivered_text = (
        "The total number of delivered story points was {0:d}."
        "".format(delivery_summary["delivery"]))
    ratio_text = (
        "The sprint delivery ratio is {0:f}%."
        "".format(delivery_summary["delivery ratio"]))

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
                    text=committed_originally_text,
                    stylename=doc.getStyleByName("Mobica Default"))),
            cjm.report.add_elements(
                odf.text.ListItem(),
                cjm.report.add_elements(
                    odf.text.P(stylename=doc.getStyleByName("Mobica Default")),
                    odf.text.Span(
                        text=committed_final_text_1,
                        stylename=doc.getStyleByName("Strong Emphasis")),
                    odf.text.Span(
                        text=committed_final_text_2))),
            cjm.report.add_elements(
                odf.text.ListItem(),
                odf.text.P(
                    text=delivered_text,
                    stylename=doc.getStyleByName("Mobica Default"))),
            cjm.report.add_elements(
                odf.text.ListItem(),
                odf.text.P(
                    text=ratio_text,
                    stylename=doc.getStyleByName("Mobica Important")))))


def append_tasks_section(cfg, doc, delivery_data):
    """Add delivered tasks table section"""

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
            odf.style.TableColumnProperties(columnwidth="3in")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.Issues.C", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="0.9in")),
        cjm.report.add_elements(
            odf.style.Style(name="Table.Issues.E", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="0.9in")),
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
        outcome = {
            "done": "done",
            "open": "not done",
            "drop": "dropped"}.get(issue["outcome"], "")
        income = {
            "extend": " (extended)",
            "commit": ""}.get(issue["income"], "")

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
                    text="{0:d}".format(issue["committed story points"]))),
            cjm.report.add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.y")),
                odf.text.P(
                    stylename=doc.getStyleByName("Mobica Table Cell Right"),
                    text="{0:d}".format(issue["delivered story points"]))),
            cjm.report.add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.y")),
                odf.text.P(
                    stylename=doc.getStyleByName("Mobica Table"),
                    text="{0:s}{1:s}".format(outcome, income))))

    cjm.report.add_elements(
        doc.text,
        odf.text.H(
            outlinelevel=2, stylename=doc.getStyleByName("Mobica Heading 2"),
            text="Task List"),
        cjm.report.add_elements(
            odf.table.Table(stylename="Table.Issues"),
            odf.table.TableColumn(stylename="Table.Issues.A"),
            odf.table.TableColumn(stylename="Table.Issues.B"),
            odf.table.TableColumn(stylename="Table.Issues.C", numbercolumnsrepeated=2),
            odf.table.TableColumn(stylename="Table.Issues.E"),
            cjm.report.add_elements(
                odf.table.TableHeaderRows(),
                cjm.report.add_elements(
                    odf.table.TableRow(stylename=doc.getStyleByName("Table.Issues.y")),
                    cjm.report.add_elements(
                        odf.table.TableCell(
                            stylename=doc.getStyleByName("Table.Issues.x.1"),
                            numberrowsspanned=2),
                        odf.text.P(
                            text="Task Id",
                            stylename=doc.getStyleByName("Mobica Table Header Left"))),
                    cjm.report.add_elements(
                        odf.table.TableCell(
                            stylename=doc.getStyleByName("Table.Issues.x.1"),
                            numberrowsspanned=2),
                        odf.text.P(
                            text="Task Title",
                            stylename=doc.getStyleByName("Mobica Table Header Left"))),
                    cjm.report.add_elements(
                        odf.table.TableCell(
                            stylename=doc.getStyleByName("Table.Issues.x.1"),
                            numbercolumnsspanned=3),
                        odf.text.P(
                            text="Story Points",
                            stylename=doc.getStyleByName("Mobica Table Header Center"))),
                    odf.table.CoveredTableCell(),
                    odf.table.CoveredTableCell()),
                cjm.report.add_elements(
                    odf.table.TableRow(stylename=doc.getStyleByName("Table.Issues.y")),
                    odf.table.CoveredTableCell(),
                    odf.table.CoveredTableCell(),
                    cjm.report.add_elements(
                        odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.1")),
                        odf.text.P(text="Committed", stylename="Mobica Table Header Small Right")),
                    cjm.report.add_elements(
                        odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.1")),
                        odf.text.P(text="Delivered", stylename="Mobica Table Header Small Right")),
                    cjm.report.add_elements(
                        odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.1")),
                        odf.text.P(text="Note", stylename="Mobica Table Header Small Left")))),
            *[__make_row(issue) for issue in delivery_data["issues"]],
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
                        formula="SUM(<C3:C{0:d}>)".format(len(delivery_data["issues"])+2)),
                    odf.text.P(
                        stylename=doc.getStyleByName("Mobica Table Header Right"))),
                cjm.report.add_elements(
                    odf.table.TableCell(
                        stylename=doc.getStyleByName("Table.Issues.x.1"),
                        valuetype="float",
                        formula="SUM(<D3:D{0:d}>)".format(len(delivery_data["issues"])+2)),
                    odf.text.P(
                        stylename=doc.getStyleByName("Mobica Table Header Right"))),
                odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.1")))))


def generate_odt_document(cfg, sprint_data, capacity_data, commitment_data, delivery_data):
    """Main function generating the delivery report document"""
    print("Report template: {0:s}".format(cfg["path"]["report template"]))

    doc = odf.opendocument.load(cfg["path"]["report template"])
    doc.text.childNodes = []

    total_committed = delivery_data["total"]["committed"]
    total_delivered = delivery_data["total"]["delivered"]
    delivery_summary = cjm.delivery.determine_summary(total_delivered, total_committed)
    team_capacity = cjm.capacity.process_team_capacity(sprint_data, capacity_data)

    cjm.report.append_doc_title(cfg, doc, sprint_data, "Delivery")
    append_head_table(cfg, doc, sprint_data, delivery_summary, team_capacity)
    append_summary_section(doc, commitment_data, delivery_summary)
    append_tasks_section(cfg, doc, delivery_data)

    doc.save(cfg["path"]["output"])

    print("Report saved to: {0:s}".format(cfg["path"]["output"]))


def main(options, defaults):
    """Entry function"""
    cfg = cjm.report.apply_options(
        cjm.cfg.apply_config(cjm.cfg.init_defaults(), defaults), options)

    cfg["path"]["output"] = options.output_file_path
    cfg["client"]["name"] = options.client_name

    sprint_data = cjm.data.load(cfg, options.sprint_file, "sprint.json")

    cfg["sprint"]["start date"] = dateutil.parser.parse(sprint_data["start date"]).date()
    cfg["sprint"]["end date"] = dateutil.parser.parse(sprint_data["end date"]).date()

    cjm.sprint.apply_data_file_paths(cfg, sprint_data)

    capacity_data = cjm.data.load(cfg, cfg["path"]["capacity"], "capacity.json")
    commitment_data = cjm.data.load(cfg, cfg["path"]["commitment"], "commitment.json")
    delivery_data = cjm.data.load(cfg, cfg["path"]["delivery"], "delivery.json")

    generate_odt_document(cfg, sprint_data, capacity_data, commitment_data, delivery_data)

    return cjm.codes.NO_ERROR


if __name__ == "__main__":
    cjm.run.run_2(main, parse_options)
