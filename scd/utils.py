import textwrap


def trim_multiline_str(string):
    return textwrap.dedent(string).strip()
