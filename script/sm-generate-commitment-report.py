#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command line script generating commitment report odt file"""

# Standard library imports
import datetime
import os
import sys

# Third party imports
import dateutil.parser
import numpy
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
import cjm.request
import cjm.run
import cjm.schema
import cjm.sprint


_ISO_DATE_STYLENAME = "N121"


def parse_options(args):
    """Parse command line options"""
    defaults = cjm.cfg.load_defaults()
    parser = cjm.cfg.make_common_parser(defaults)

    default_output_file_path = "commitment_report.odt"
    default_client_name = defaults.get("client", {}).get("name", "INTEL")

    parser.add_argument(
        "sprint_file", action="store",
        help=(
            "Path to the json sprint data file as generated by the {0:s} script and described by"
            " the {1:s} schema"
            "".format(cjm.SM_CREATE_SPRINT_FILE, cjm.schema.make_subpath("sprint.json"))))

    parser.add_argument(
        "capacity_file", action="store",
        help=(
            "Path to the json capacity data file as generated by the {0:s} script and described"
            " by the {1:s} schema"
            "".format(cjm.SM_CREATE_CAPACITY_FILE, cjm.schema.make_subpath("capacity.json"))))

    parser.add_argument(
        "commitment_file", action="store",
        help=(
            "Path to the json commitment data file as generated by the {0:s} script and described"
            " by the {1:s} schema"
            "".format(cjm.SM_CREATE_COMMITMENT_FILE, cjm.schema.make_subpath("commitment.json"))))

    parser.add_argument(
        "-o", "--output-file", action="store", metavar="PATH", dest="output_file_path",
        default=default_output_file_path,
        help=(
            "PATH to the output file into which the odt document will be written"
            " (default: '{0:s}')".format(default_output_file_path)))

    parser.add_argument(
        "--client", action="store", metavar="NAME", dest="client_name",
        default=default_client_name,
        help=(
            "NAME of the client{0:s}".format(cjm.cfg.fmt_dft(default_client_name))))

    return parser.parse_args(args)


def get_report_author(cfg):
    """Request full name of the current user"""
    current_user_url = cjm.request.make_cj_gadget_url(cfg, "currentUser")
    response = cjm.request.make_cj_request(cfg, current_user_url)
    current_user_json = response.json()

    return current_user_json["fullName"]


def remove_meta_element(doc, namespace, local_part):
    """Remove meta element specified by local_part name from the given document"""
    doc.meta.childNodes[:] = [
        e for e in doc.meta.childNodes if e.qname != (namespace, local_part)]


def add_elements(parent_element, *elements):
    """Add given xml dom elements to the parent element and then return it"""
    for element in elements:
        parent_element.addElement(element)
    return parent_element


def append_doc_title(cfg, doc, sprint_data):
    """Add document title"""
    title = "Mobica {0:s} Sprint Commitment ({1:s})".format(
        sprint_data["project"]["name"],
        _get_sprint_weeks(cfg))

    remove_meta_element(doc, odf.namespaces.DCNS, "title")
    doc.meta.addElement(odf.dc.Title(text=title))

    add_elements(
        doc.text,
        add_elements(
            odf.text.H(outlinelevel=1, stylename=doc.getStyleByName("Mobica Heading 1")),
            odf.text.Title()))

def _get_sprint_weeks(cfg):
    return cjm.sprint.generate_sprint_period_name(
        cfg["sprint"]["start date"], cfg["sprint"]["end date"])


def append_head_table(cfg, doc, sprint_data):
    """Add document header table"""

    def __get_duration(sprint_data):
        return "{0:s} to {1:s}".format(sprint_data["start date"], sprint_data["end date"])

    def __get_workdays(cfg):
        return numpy.busday_count(cfg["sprint"]["start date"], cfg["sprint"]["end date"]).item()

    rows = (
        ("Client", cfg["client"]["name"]),
        ("Project", sprint_data["project"]["name"]),
        ("Sprint Weeks", _get_sprint_weeks(cfg)),
        ("Sprint Duration", __get_duration(sprint_data)),
        ("Sprint Workdays", __get_workdays(cfg)),
        ("Report Author", get_report_author(cfg)),
        ("Report Date", "CURRENT_DATE"))

    def __make_row(spec):
        cpt, val = spec

        if val != "CURRENT_DATE":
            val_p = odf.text.P(text=val, stylename=doc.getStyleByName("Mobica Table Cell"))
        else:
            val_p = add_elements(
                odf.text.P(stylename=doc.getStyleByName("Mobica Table Cell")),
                odf.text.Date(
                    datastylename=_ISO_DATE_STYLENAME,
                    datevalue=datetime.datetime.utcnow().isoformat()))

        return add_elements(
            odf.table.TableRow(),
            add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table1.A.x")),
                odf.text.P(text=cpt, stylename=doc.getStyleByName("Mobica Table Header Left"))),
            add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table1.B.x")),
                val_p))

    add_elements(
        doc.automaticstyles,
        add_elements(
            odf.style.Style(name="Table1.A", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="1.7in")),
        add_elements(
            odf.style.Style(name="Table1.A", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="5in")))

    add_elements(
        doc.automaticstyles,
        add_elements(
            odf.style.Style(name="Table1.A.x", family="table-cell"),
            make_caption_cell_props()),
        add_elements(
            odf.style.Style(name="Table1.B.x", family="table-cell"),
            make_value_cell_props()))

    add_elements(
        doc.text,
        add_elements(
            odf.table.Table(),
            odf.table.TableColumn(numbercolumnsrepeated=1, stylename="Table1.A"),
            odf.table.TableColumn(numbercolumnsrepeated=1, stylename="Table1.B"),
            *[__make_row(spec) for spec in rows]))


def append_summary_section(doc, sprint_data, capacity_data, commitment_data):
    """Add commitment summary section"""

    committed_text = (
        "The total number of committed story points is {0:d}."
        "".format(commitment_data["total"]["committed"]))
    capacity_text = (
        "The sprint capacity is {0:d} story points."
        "".format(_calc_team_capacity(sprint_data, capacity_data)))

    add_elements(
        doc.text,
        odf.text.H(
            outlinelevel=2, stylename=doc.getStyleByName("Mobica Heading 2"),
            text="Summary"),
        add_elements(
            odf.text.List(stylename="L1"),
            add_elements(
                odf.text.ListItem(),
                odf.text.P(
                    stylename=doc.getStyleByName("Mobica Important"),
                    text=committed_text)),
            add_elements(
                odf.text.ListItem(),
                odf.text.P(
                    stylename=doc.getStyleByName("Mobica Default"),
                    text=capacity_text))))


def make_caption_cell_props():
    """Create table cell properties object for caption cells"""

    tcp = odf.style.TableCellProperties()
    tcp.setAttrNS(odf.namespaces.FONS, "background-color", "#99ccff")
    tcp.setAttrNS(odf.namespaces.FONS, "padding", "0.0382in")
    tcp.setAttrNS(odf.namespaces.FONS, "border", "0.05pt solid #000000")
    return tcp


def make_value_cell_props():
    """Create table cell properties object for value cells"""

    tcp = odf.style.TableCellProperties()
    tcp.setAttrNS(odf.namespaces.FONS, "padding", "0.0382in")
    tcp.setAttrNS(odf.namespaces.FONS, "border", "0.05pt solid #000000")
    return tcp


def append_tasks_section(cfg, doc, commitment_data):
    """Add commitment tasks table section"""

    add_elements(
        doc.automaticstyles,
        add_elements(
            odf.style.Style(name="Table.Issues", family="table"),
            odf.style.TableProperties(width="6.7in", align="margins")),
        add_elements(
            odf.style.Style(name="Table.Issues.A", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="1in")),
        add_elements(
            odf.style.Style(name="Table.Issues.B", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="4.6in")),
        add_elements(
            odf.style.Style(name="Table.Issues.C", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="1.1in")),
        add_elements(
            odf.style.Style(name="Table.Issues.y", family="table-row"),
            odf.style.TableRowProperties(keeptogether="always")),
        add_elements(
            odf.style.Style(name="Table.Issues.x.1", family="table-cell"),
            make_caption_cell_props()),
        add_elements(
            odf.style.Style(name="Table.Issues.x.y", family="table-cell"),
            make_value_cell_props()))

    def __make_row(issue):
        issue_url = cjm.request.make_cj_issue_url(cfg, str(issue["key"]))

        return add_elements(
            odf.table.TableRow(stylename=doc.getStyleByName("Table.Issues.y")),
            add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.y")),
                add_elements(
                    odf.text.P(stylename=doc.getStyleByName("Mobica Table Cell")),
                    odf.text.A(
                        stylename=doc.getStyleByName("Internet link"),
                        visitedstylename=doc.getStyleByName("Visited Internet Link"),
                        href=issue_url,
                        text=issue["key"]))),
            add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.y")),
                odf.text.P(
                    stylename=doc.getStyleByName("Mobica Table Cell"),
                    text=issue["summary"])),
            add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.y")),
                odf.text.P(
                    stylename=doc.getStyleByName("Mobica Table Cell Right"),
                    text=issue["story points"])))

    add_elements(
        doc.text,
        odf.text.H(
            outlinelevel=2, stylename=doc.getStyleByName("Mobica Heading 2"),
            text="Committed Task List"),
        add_elements(
            odf.table.Table(stylename="Table.Issues"),
            odf.table.TableColumn(numbercolumnsrepeated=1, stylename="Table.Issues.A"),
            odf.table.TableColumn(numbercolumnsrepeated=1, stylename="Table.Issues.B"),
            odf.table.TableColumn(numbercolumnsrepeated=1, stylename="Table.Issues.C"),
            add_elements(
                odf.table.TableHeaderRows(),
                add_elements(
                    odf.table.TableRow(stylename=doc.getStyleByName("Table.Issues.y")),
                    add_elements(
                        odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.1")),
                        odf.text.P(
                            text="Task Id",
                            stylename=doc.getStyleByName("Mobica Table Header Left"))),
                    add_elements(
                        odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.1")),
                        odf.text.P(
                            text="Task Title",
                            stylename=doc.getStyleByName("Mobica Table Header Left"))),
                    add_elements(
                        odf.table.TableCell(stylename=doc.getStyleByName("Table.Issues.x.1")),
                        odf.text.P(
                            text="Story Points",
                            stylename=doc.getStyleByName("Mobica Table Header Right"))))),
            *[__make_row(issue) for issue in commitment_data["issues"]],
            add_elements(
                odf.table.TableRow(stylename=doc.getStyleByName("Table.Issues.y")),
                add_elements(
                    odf.table.TableCell(
                        stylename=doc.getStyleByName("Table.Issues.x.1"),
                        numbercolumnsspanned="2"),
                    odf.text.P(
                        text="Total:",
                        stylename=doc.getStyleByName("Mobica Table Header Right"))),
                odf.table.CoveredTableCell(),
                add_elements(
                    odf.table.TableCell(
                        stylename=doc.getStyleByName("Table.Issues.x.1"),
                        valuetype="float",
                        formula="SUM(<C2:C{0:d}>)".format(len(commitment_data["issues"]))),
                    odf.text.P(
                        stylename=doc.getStyleByName("Mobica Table Header Right"))))))


def generate_odt_document(cfg, capacity_data, commitment_data, sprint_data):
    """Main function generating the commitment report document"""
    output_doc = odf.opendocument.load(
        os.path.join(cfg["path"]["data"], "odt", "report-template.odt"))
    output_doc.text.childNodes = []

    append_doc_title(cfg, output_doc, sprint_data)
    append_head_table(cfg, output_doc, sprint_data)
    append_summary_section(output_doc, sprint_data, capacity_data, commitment_data)
    append_tasks_section(cfg, output_doc, commitment_data)

    output_doc.save(cfg["path"]["output"])


def _calc_team_capacity(sprint_data, capacity_data):
    team_capacity = cjm.capacity.process_team_capacity(sprint_data, capacity_data)
    return sum(
        cjm.capacity.process_person_capacity(team_capacity, p)["sprint capacity"]
        for p in capacity_data["people"])


def main(options):
    """Entry function"""
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)
    cfg["path"]["output"] = options.output_file_path
    cfg["client"]["name"] = options.client_name

    capacity_data = cjm.data.load(cfg, options.capacity_file, "capacity.json")
    commitment_data = cjm.data.load(cfg, options.commitment_file, "commitment.json")
    sprint_data = cjm.data.load(cfg, options.sprint_file, "sprint.json")

    cfg["sprint"]["start date"] = dateutil.parser.parse(sprint_data["start date"]).date()
    cfg["sprint"]["end date"] = dateutil.parser.parse(sprint_data["end date"]).date()

    generate_odt_document(cfg, capacity_data, commitment_data, sprint_data)

    return cjm.codes.NO_ERROR


if __name__ == "__main__":
    cjm.run.run(main, parse_options(sys.argv[1:]))
