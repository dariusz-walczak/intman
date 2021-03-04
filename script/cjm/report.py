"""ODF report generation helpers and shared functions"""

# Standard library imports
import copy
import datetime

# Third party imports
import odf.dc
import odf.namespaces
import odf.text

# Project imports
import cjm.sprint


ISO_DATE_STYLENAME = "N121"


def add_elements(parent_element, *elements):
    """Add given xml dom elements to the parent element and then return it"""
    for element in elements:
        parent_element.addElement(element)
    return parent_element


def join_elements(parent_element, glue_element, *elements):
    """Add given xml dom elements to the parent element and interleave them with the glue element.
    Return the parent element"""
    for element in elements[:-1]:
        add_elements(parent_element, element, copy.copy(glue_element))

    add_elements(parent_element, elements[-1])

    return parent_element

def create_issue_anchor_element(cfg, doc, issue_key):
    """Create xml dom anchor linking to specified issue"""
    return odf.text.A(
        stylename=doc.getStyleByName("Internet link"),
        visitedstylename=doc.getStyleByName("Visited Internet Link"),
        href=cjm.request.make_cj_issue_url(cfg, issue_key),
        text=issue_key)


def append_doc_title(cfg, doc, sprint_data, report_type):
    """Add report document title"""
    title = "Mobica {0:s} Sprint {1:s} ({2:s})".format(
        sprint_data["project"]["name"], report_type,
        make_sprint_period_val(cfg))

    remove_meta_element(doc, odf.namespaces.DCNS, "title")
    doc.meta.addElement(odf.dc.Title(text=title))

    add_elements(
        doc.text,
        add_elements(
            odf.text.H(outlinelevel=1, stylename=doc.getStyleByName("Mobica Heading 1")),
            odf.text.Title()))


def make_caption_ver_cell_props():
    """Create table cell properties object for vertical caption cells"""

    tcp = odf.style.TableCellProperties()
    tcp.setAttrNS(odf.namespaces.FONS, "background-color", "#99ccff")
    tcp.setAttrNS(odf.namespaces.FONS, "padding", "0.0382in")
    tcp.setAttrNS(odf.namespaces.FONS, "border", "0.05pt solid #000000")
    return tcp

def make_caption_hor_cell_props():
    """Create table cell properties object for horizontal caption cells"""

    tcp = odf.style.TableCellProperties()
    tcp.setAttrNS(odf.namespaces.FONS, "background-color", "#99ccff")
    tcp.setAttrNS(odf.namespaces.FONS, "padding", "0.0382in")
    tcp.setAttrNS(odf.namespaces.FONS, "border", "0.05pt solid #000000")
    tcp.setAttrNS(odf.namespaces.STYLENS, "vertical-align", "middle")
    return tcp


def make_value_cell_props():
    """Create table cell properties object for value cells"""

    tcp = odf.style.TableCellProperties()
    tcp.setAttrNS(odf.namespaces.FONS, "padding", "0.0382in")
    tcp.setAttrNS(odf.namespaces.FONS, "border", "0.05pt solid #000000")
    return tcp


def make_sprint_duration_val(sprint_data):
    """Compose sprint duration value to be put into the report head table"""
    return "{0:s} to {1:s}".format(sprint_data["start date"], sprint_data["end date"])


def make_sprint_period_val(cfg):
    """Compose sprint period name to be put into the report head table"""
    return cjm.sprint.generate_sprint_period_name(
        cfg, cfg["sprint"]["start date"], cfg["sprint"]["end date"])


def make_sprint_workdays_val(capacity_data):
    """Compose sprint workday value to be put into the report head table"""
    return capacity_data["workday count"] - len(capacity_data["shared holidays"])


def make_current_date_cell_val_cb():
    """Create a callback returning current date paragraph to be used optionally used with one of
    the append_head_table data_rows"""
    return lambda doc: add_elements(
        odf.text.P(stylename=doc.getStyleByName("Mobica Table Cell")),
        odf.text.Date(
            datastylename=ISO_DATE_STYLENAME,
            datevalue=datetime.datetime.utcnow().isoformat()))


def append_head_table(doc, data_rows):
    """Add document header table"""

    cjm.report.add_elements(
        doc.automaticstyles,
        cjm.report.add_elements(
            odf.style.Style(name="Table1.A", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="1.7in")),
        cjm.report.add_elements(
            odf.style.Style(name="Table1.A", family="table-column"),
            odf.style.TableColumnProperties(columnwidth="5in")),
        cjm.report.add_elements(
            odf.style.Style(name="Table1.A.x", family="table-cell"),
            make_caption_ver_cell_props()),
        cjm.report.add_elements(
            odf.style.Style(name="Table1.B.x", family="table-cell"),
            make_value_cell_props()))

    def __make_row(spec):
        cpt, val = spec

        if callable(val):
            val_p = val(doc)
        else:
            val_p = odf.text.P(text=val, stylename=doc.getStyleByName("Mobica Table Cell"))

        return cjm.report.add_elements(
            odf.table.TableRow(),
            cjm.report.add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table1.A.x")),
                odf.text.P(text=cpt, stylename=doc.getStyleByName("Mobica Table Header Left"))),
            cjm.report.add_elements(
                odf.table.TableCell(stylename=doc.getStyleByName("Table1.B.x")),
                val_p))

    add_elements(
        doc.text,
        add_elements(
            odf.table.Table(),
            odf.table.TableColumn(numbercolumnsrepeated=1, stylename="Table1.A"),
            odf.table.TableColumn(numbercolumnsrepeated=1, stylename="Table1.B"),
            *[__make_row(spec) for spec in data_rows]))


def remove_meta_element(doc, namespace, local_part):
    """Remove meta element specified by local_part name from the given document"""
    doc.meta.childNodes[:] = [
        e for e in doc.meta.childNodes if e.qname != (namespace, local_part)]
