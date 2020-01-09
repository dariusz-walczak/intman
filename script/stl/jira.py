import re

def sort_key(key):
    m = re.match("^(?P<qual>[A-Z0-9]+)-(?P<num>[0-9]+)$", key)

    if m is not None:
        return (m.group("qual"), int(m.group("num")))
    else:
        return ("", 0)


