import platform


def adjust_separator_for_pac(originstring):
    """
    convert a string cointaining "/" path separators (i.e. unix filname)
    to a string containing "\" path separators (as used by the .pac file directory)
    """
    return originstring.replace("/", "\\")


def adjust_separator_for_fs(originstring):
    """
    convert a string containing "\" path separators (as used by the .pac file directory)
    to a string containing the os specific path separator
    """
    if platform.system() == "Windows":
        return originstring.replace("/", "\\")
    else:
        return originstring.replace("\\", "/")
