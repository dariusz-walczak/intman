def generate_sprint_name(project_name, start_dt, end_dt):
    _, start_ww, _ = start_dt.isocalendar()
    _, end_ww, _ = end_dt.isocalendar()

    return "{0:s} WW{1:02d}-WW{2:02d}".format(project_name, start_ww, end_ww)
