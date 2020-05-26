#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command line script generating commitment report odt file"""

# Standard library imports
import os
import sys
import datetime as dt

# Third party imports
import holidays
import numpy

import odf.text
import odf.dc
import odf.draw
import odf.opendocument
import odf.style
import odf.table

# Project imports
import cjm
import cjm.cfg
import cjm.request
import cjm.codes
import cjm.schema
import cjm.sprint
import cjm.commitment


def parse_options(args):
    """Parse command line options"""
    defaults = cjm.cfg.load_defaults()
    parser = cjm.cfg.make_common_parser(defaults)

    default_output_file_path = "commitment_report.odt"
    default_client_name = "CLIENT"

    parser.add_argument(
        "sprint_file", action="store",
        help=(
            "Path to the json sprint data file as generated by the {0:s} script and described by"
            " the {1:s} schema"
            "".format(cjm.SM_CREATE_SPRINT_FILE, cjm.schema.make_subpath("sprint.json"))))

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
            " (default: '{0:s}')".format(default_output_file_path)
        )
    )

    parser.add_argument(
        "--client", action="store", metavar="NAME", dest="client_name",
        default=default_client_name,
        help=(
            "NAME of the client"
            " (default: '{0:s}')".format(default_client_name)
        )
    )

    return parser.parse_args(args)


def calculate_workdays(start_date, end_date):
    """Return number of workdays between given dates"""
    start_year = int(start_date.split("-")[0])
    end_year = int(end_date.split("-")[0])

    # NOTE: https://community.developer.atlassian.com/t/rest-api-getting-non-working-days/9851
    # "(...) there is no direct way to fetch working and non-working days for given board."

    pl_holidays = []
    for date, _ in holidays.PL(years=[start_year, end_year]).items():
        pl_holidays.append(numpy.datetime64(date))

    workdays = numpy.busday_count(
        numpy.datetime64(start_date), numpy.datetime64(end_date), holidays=pl_holidays)
    return workdays


def get_report_author(cfg):
    """Request full name of the current user"""
    current_user_url = cjm.request.make_cj_gadget_url(cfg, "currentUser")
    response = cjm.request.make_cj_request(cfg, current_user_url)
    current_user_json = response.json()

    return current_user_json["fullName"]


def logo(cfg, textdoc):
    """Add Mobica logo"""
    style = add_style(textdoc, "style")

    logo_frame = odf.draw.Frame(
        width="2.7cm", height="2.7cm", x="0cm", y="0cm", anchortype="as-char", stylename=style)
    href = textdoc.addPicture(os.path.join(cfg["path"]["data"], "odt", "logo.jpg"))
    logo_frame.addElement(odf.draw.Image(href=href))
    textdoc.text.addElement(logo_frame)


def data_table(cfg, textdoc, sprint_data):
    """Create header table"""
    title_style = add_style(textdoc, "title_style")
    title_cell_style = add_style(textdoc, "title_cell_style")
    tab1_w1 = add_style(textdoc, "tab1_w1")
    tab1_w2 = add_style(textdoc, "tab1_w2")
    desc_cell_style = add_style(textdoc, "desc_cell_style")

    project_title, project_workweek = sprint_data["name"].split(" ")
    title = "Mobica " + project_title + " sprint commitment (" + project_workweek + ")"

    h = odf.text.H(outlinelevel=1, stylename=title_style, text=title)
    textdoc.meta.addElement(odf.dc.Title(text=title))
    textdoc.text.addElement(h)

    textdoc.text.addElement(odf.text.P())

    table = odf.table.Table()
    table.addElement(odf.table.TableColumn(numbercolumnsrepeated=1, stylename=tab1_w1))
    table.addElement(odf.table.TableColumn(numbercolumnsrepeated=1, stylename=tab1_w2))

    tr = odf.table.TableRow()
    table.addElement(tr)

    tc1 = odf.table.TableCell()
    tr.addElement(tc1)
    p = odf.text.P(stylename=title_cell_style, text="Client")
    tc1.addElement(p)

    tc2 = odf.table.TableCell()
    tr.addElement(tc2)
    p = odf.text.P(stylename=desc_cell_style, text=cfg["client"]["name"])
    tc2.addElement(p)

    tr = odf.table.TableRow()
    table.addElement(tr)

    tc1 = odf.table.TableCell()
    tr.addElement(tc1)
    p = odf.text.P(stylename=title_cell_style, text="Project")
    tc1.addElement(p)

    tc2 = odf.table.TableCell()
    tr.addElement(tc2)
    p = odf.text.P(stylename=desc_cell_style, text=project_title)
    tc2.addElement(p)

    tr = odf.table.TableRow()
    table.addElement(tr)

    tc1 = odf.table.TableCell()
    tr.addElement(tc1)
    p = odf.text.P(stylename=title_cell_style, text="Sprint Weeks")
    tc1.addElement(p)

    tc2 = odf.table.TableCell()
    tr.addElement(tc2)
    p = odf.text.P(stylename=desc_cell_style, text=project_workweek)
    tc2.addElement(p)

    tr = odf.table.TableRow()
    table.addElement(tr)

    tc1 = odf.table.TableCell()
    tr.addElement(tc1)
    p = odf.text.P(stylename=title_cell_style, text="Sprint Duration")
    tc1.addElement(p)

    tc2 = odf.table.TableCell()
    tr.addElement(tc2)
    p = odf.text.P(
        stylename=desc_cell_style,
        text="{0:s} to {1:s}".format(sprint_data["start date"], sprint_data["end date"]))
    tc2.addElement(p)

    tr = odf.table.TableRow()
    table.addElement(tr)

    tc1 = odf.table.TableCell()
    tr.addElement(tc1)
    p = odf.text.P(stylename=title_cell_style, text="Sprint Workdays")
    tc1.addElement(p)

    tc2 = odf.table.TableCell()
    tr.addElement(tc2)
    p = odf.text.P(stylename=desc_cell_style, text=calculate_workdays(sprint_data["start date"],
                                                                      sprint_data["end date"]))
    tc2.addElement(p)

    tr = odf.table.TableRow()
    table.addElement(tr)

    tc1 = odf.table.TableCell()
    tr.addElement(tc1)
    p = odf.text.P(stylename=title_cell_style, text="Report Author")
    tc1.addElement(p)

    tc2 = odf.table.TableCell()
    tr.addElement(tc2)
    p = odf.text.P(stylename=desc_cell_style, text=get_report_author(cfg))
    tc2.addElement(p)

    tr = odf.table.TableRow()
    table.addElement(tr)

    tc1 = odf.table.TableCell()
    tr.addElement(tc1)
    p = odf.text.P(stylename=title_cell_style, text="Report Date")
    tc1.addElement(p)

    tc2 = odf.table.TableCell()
    tr.addElement(tc2)
    p = odf.text.P(stylename=desc_cell_style, text=dt.datetime.today().strftime('%d-%m-%Y'))
    tc2.addElement(p)

    textdoc.text.addElement(table)


def summary(textdoc, commitment_data):
    """Generate summary points"""
    title2_style = add_style(textdoc, "title2_style")
    default_bold_style = add_style(textdoc, "default_bold_style")
    default_style = add_style(textdoc, "default_style")

    h2 = odf.text.H(outlinelevel=1, stylename=title2_style, text="Summary")
    textdoc.text.addElement(h2)
    textdoc.text.addElement(odf.text.P())

    p = odf.text.P(
        stylename=default_bold_style, text=(
            "- The total number of committed story points is {0:d}."
            "".format(commitment_data["total"]["committed"])))
    textdoc.text.addElement(p)

    sprint_capacity = 0
    p = odf.text.P(
        stylename=default_style, text=(
            "- The sprint capacity is {0:d} story points."
            "".format(sprint_capacity)))
    textdoc.text.addElement(p)


def committed_tasks_list(cfg, textdoc, commitment_data):
    """Generate table with committed tasks"""
    title2_style = add_style(textdoc, "title2_style")
    title_cell_style = add_style(textdoc, "title_cell_style")
    desc_cell_style = add_style(textdoc, "desc_cell_style")
    tab2_w1 = add_style(textdoc, "tab2_w1")
    tab2_w2 = add_style(textdoc, "tab2_w2")
    tab2_w3 = add_style(textdoc, "tab2_w3")

    h3 = odf.text.H(outlinelevel=1, stylename=title2_style, text="Committed Tasks List")
    textdoc.text.addElement(h3)
    textdoc.text.addElement(odf.text.P())

    table = odf.table.Table()
    table.addElement(odf.table.TableColumn(numbercolumnsrepeated=1, stylename=tab2_w1))
    table.addElement(odf.table.TableColumn(numbercolumnsrepeated=1, stylename=tab2_w2))
    table.addElement(odf.table.TableColumn(numbercolumnsrepeated=1, stylename=tab2_w3))

    table_header = odf.table.TableRow()
    table.addElement(table_header)

    tc1_top = odf.table.TableCell()
    table_header.addElement(tc1_top)
    p = odf.text.P(stylename=title_cell_style, text="Task ID")
    tc1_top.addElement(p)

    tc2_top = odf.table.TableCell()
    table_header.addElement(tc2_top)
    p = odf.text.P(stylename=title_cell_style, text="Task Title")
    tc2_top.addElement(p)

    tc3_top = odf.table.TableCell()
    table_header.addElement(tc3_top)
    p = odf.text.P(stylename=title_cell_style, text="Story Points")
    tc3_top.addElement(p)

    rows_containing_data = 1

    for issue in commitment_data["issues"]:
        tr = odf.table.TableRow()
        table.addElement(tr)

        commitment_issue_url = cjm.request.make_cj_issue_url(cfg, str(issue["key"]))

        tc1 = odf.table.TableCell()
        tr.addElement(tc1)
        p = odf.text.P()
        a = odf.text.A(stylename=desc_cell_style, href=commitment_issue_url, text=issue["key"])
        p.addElement(a)
        tc1.addElement(p)

        tc2 = odf.table.TableCell()
        tr.addElement(tc2)
        p = odf.text.P(stylename=desc_cell_style, text=issue["summary"])
        tc2.addElement(p)

        tc3 = odf.table.TableCell()
        tr.addElement(tc3)
        p = odf.text.P(stylename=desc_cell_style, text=issue["story points"])
        tc3.addElement(p)

        rows_containing_data += 1

    table_footer = odf.table.TableRow()
    table.addElement(table_footer)

    tc1_bottom = odf.table.TableCell()
    table_footer.addElement(tc1_bottom)
    p = odf.text.P(stylename=title_cell_style, text="")
    tc1_bottom.addElement(p)

    tc2_bottom = odf.table.TableCell()
    table_footer.addElement(tc2_bottom)
    p = odf.text.P(stylename=title_cell_style, text="Total:")
    tc2_bottom.addElement(p)

    tc3_bottom = odf.table.TableCell(
        stylename=title_cell_style,
        formula="SUM(<C2:C" + str(rows_containing_data) + ">)", valuetype="float")
    table_footer.addElement(tc3_bottom)

    textdoc.text.addElement(table)


def add_style(textdoc, name):
    """Define requested style and add it to the doc"""
    # STYLE
    if name == "style":
        style = odf.style.Style(name='s1', parentstylename="Graphics", family="graphic")
        style.addElement(
            odf.style.GraphicProperties(verticalpos="from-top", horizontalpos="from-left"))
        textdoc.automaticstyles.addElement(style)
        return style

    # TABLE 1 COLUMNS STYLE
    if name == "tab1_w1":
        tab1_w1 = odf.style.Style(name="w1", family="table-column")
        tab1_w1.addElement(odf.style.TableColumnProperties(columnwidth="4cm"))
        textdoc.automaticstyles.addElement(tab1_w1)
        return tab1_w1

    if name == "tab1_w2":
        tab1_w2 = odf.style.Style(name="w2", family="table-column")
        tab1_w2.addElement(odf.style.TableColumnProperties(columnwidth="13cm"))
        textdoc.automaticstyles.addElement(tab1_w2)
        return tab1_w2

    # TABLE 2 COLUMNS STYLE
    if name == "tab2_w1":
        tab2_w1 = odf.style.Style(name="w1", family="table-column")
        tab2_w1.addElement(odf.style.TableColumnProperties(columnwidth="2cm"))
        textdoc.automaticstyles.addElement(tab2_w1)
        return tab2_w1

    if name == "tab2_w2":
        tab2_w2 = odf.style.Style(name="w2", family="table-column")
        tab2_w2.addElement(odf.style.TableColumnProperties(columnwidth="12cm"))
        textdoc.automaticstyles.addElement(tab2_w2)
        return tab2_w2

    if name == "tab2_w3":
        tab2_w3 = odf.style.Style(name="w3", family="table-column")
        tab2_w3.addElement(odf.style.TableColumnProperties(columnwidth="3cm"))
        textdoc.automaticstyles.addElement(tab2_w3)
        return tab2_w3

    # TITLE STYLE
    if name == "title_style":
        title_style = odf.style.Style(name="Mobica Heading 1", family="paragraph")
        title_style.addElement(
            odf.style.TextProperties(
                attributes={'fontfamily': 'Verdana', 'fontsize': "14pt", 'fontweight': "bold"}))
        textdoc.styles.addElement(title_style)
        return title_style

    # TITLE CELL STYLE
    if name == "title_cell_style":
        title_cell_style = odf.style.Style(name="Mobica Table Header Left", family="paragraph")
        title_cell_style.addElement(odf.style.ParagraphProperties(padding="0.04in"))
        title_cell_style.addElement(
            odf.style.TextProperties(
                attributes={'fontfamily': 'Verdana', 'fontsize': "10pt", 'fontweight': "bold"}))
        title_cell_style.addElement(odf.style.GraphicProperties(fill="solid", fillcolor="#99ccff"))
        textdoc.styles.addElement(title_cell_style)
        return title_cell_style

    # DESCRIPTION CELL STYLE
    if name == "desc_cell_style":
        desc_cell_style = odf.style.Style(name="Mobica Table Cell", family="paragraph")
        desc_cell_style.addElement(odf.style.ParagraphProperties(padding="0.04in"))
        desc_cell_style.addElement(
            odf.style.TextProperties(
                attributes={'fontfamily': 'Verdana', 'fontsize': "10pt", 'fontweight': "normal"}))
        textdoc.styles.addElement(desc_cell_style)
        return desc_cell_style

    # TITLE CELL 2 STYLE
    if name == "title2_style":
        title2_style = odf.style.Style(name="Mobica Heading 2", family="paragraph")
        title2_style.addElement(
            odf.style.TextProperties(
                attributes={'fontfamily': 'Verdana', 'fontsize': "12pt", 'fontweight': "bold"}))
        textdoc.styles.addElement(title2_style)
        return title2_style

    # DEFAULT STYLE
    if name == "default_style":
        default_style = odf.style.Style(name="Default Mobica Style", family="paragraph")
        default_style.addElement(
            odf.style.TextProperties(
                attributes={'fontfamily': 'Verdana', 'fontsize': "10pt", 'fontweight': "normal"}))
        textdoc.styles.addElement(default_style)
        return default_style

    # DEFAULT STYLE BOLD
    if name == "default_bold_style":
        default_bold_style = odf.style.Style(name="Default Mobica Style Bold", family="paragraph")
        default_bold_style.addElement(
            odf.style.TextProperties(
                attributes={'fontfamily': 'Verdana', 'fontsize': "10pt", 'fontweight': "bold"}))
        textdoc.styles.addElement(default_bold_style)
        return default_bold_style

    return None

def generate_odt_document(cfg, commitment_data, sprint_data):
    """Main function generating the commitment report document"""
    textdoc = odf.opendocument.OpenDocumentText()

    logo(cfg, textdoc)

    for _ in range(4):
        textdoc.text.addElement(odf.text.P())

    data_table(cfg, textdoc, sprint_data)

    for _ in range(1):
        textdoc.text.addElement(odf.text.P())

    summary(textdoc, commitment_data)

    for _ in range(2):
        textdoc.text.addElement(odf.text.P())

    committed_tasks_list(cfg, textdoc, commitment_data)

    textdoc.save(cfg["path"]["output"])


def main(options):
    """Entry function"""
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)
    cfg["path"]["output"] = options.output_file_path
    cfg["client"]["name"] = options.client_name

    commitment_data = cjm.data.load(cfg, options.commitment_file, "commitment.json")
    sprint_data = cjm.data.load(cfg, options.sprint_file, "sprint.json")

    generate_odt_document(cfg, commitment_data, sprint_data)

    return cjm.codes.NO_ERROR


if __name__ == "__main__":
    cjm.run.run(main, parse_options(sys.argv[1:]))
