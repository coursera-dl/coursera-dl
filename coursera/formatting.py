import os

from .define import FORMAT_MAX_LENGTH, TITLE_MAX_LENGTH


def format_section(num, section, class_name, verbose_dirs):
    sec = "%02d_%s" % (num, section)
    if verbose_dirs:
        sec = class_name.upper() + "_" + sec
    return sec


def format_resource(num, name, title, fmt):
    if title:
        title = "_" + title
    return "%02d_%s%s.%s" % (num, name, title, fmt)


def format_combine_number_resource(secnum, lecnum, lecname, title, fmt):
    if title:
        title = "_" + title
    return "%02d_%02d_%s%s.%s" % (secnum, lecnum, lecname, title, fmt)


def get_lecture_filename(
    combined_section_lectures_nums, section_dir, secnum, lecnum, lecname, title, fmt
):
    """
    Prepare a destination lecture filename.

    @param combined_section_lectures_nums: Flag that indicates whether
        section lectures should have combined numbering.
    @type combined_section_lectures_nums: bool

    @param section_dir: Path to current section directory.
    @type section_dir: str

    @param secnum: Section number.
    @type secnum: int

    @param lecnum: Lecture number.
    @type lecnum: int

    @param lecname: Lecture name.
    @type lecname: str

    @param title: Resource title.
    @type title: str

    @param fmt: Format of the resource (pdf, csv, etc)
    @type fmt: str

    @return: Lecture file name.
    @rtype: str
    """
    # FIXME: this is a quick and dirty solution to Filename too long
    # problem. We need to think of a more general way to solve this
    # issue.
    fmt = fmt[:FORMAT_MAX_LENGTH]
    title = title[:TITLE_MAX_LENGTH]

    # Format lecture file name
    if combined_section_lectures_nums:
        lecture_filename = os.path.join(
            section_dir,
            format_combine_number_resource(secnum + 1, lecnum + 1, lecname, title, fmt),
        )
    else:
        lecture_filename = os.path.join(
            section_dir, format_resource(lecnum + 1, lecname, title, fmt)
        )

    return lecture_filename
