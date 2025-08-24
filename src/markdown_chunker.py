import re
from typing import TypedDict


def chunk_markdown_by_heading(markdown: str) -> list[str]:
    """
    Splits the given markdown string into sections based on headings.
    Each section is a string with the content of the section.

    Child sections are included in their parent section.
    """

    class Section(TypedDict):
        heading: str
        level: int
        result: str | None

    lines = markdown.splitlines()
    sections: list[Section] = []
    current: Section | None = None
    temporary_content: list[str] = []

    # build a list with all direct data of the given sections (meaning parent headings have no child content)
    for line in lines:
        # match headings beginning with repeated `#`
        match = re.match(r"^(#{1,6}) (.+)", line)
        if match:
            if current:
                current["result"] = "\n".join(temporary_content).strip()
                sections.append(current)

            # store initial heading and clear previous temporary content
            temporary_content = [line]
            current = {
                "heading": match[2].strip(),
                "level": len(match[1]),
                "result": None,
            }
        elif current:
            temporary_content.append(line)

    # add the last section
    if current:
        current["result"] = "\n".join(temporary_content).strip()
        sections.append(current)

    # enhance lists, to let parents include their children, based on ordering
    chunked_markdown: list[str] = []
    for i, section in enumerate(sections):
        initial_level = section["level"]
        current_section: list[Section] = []

        # only iterate over following sections, as children can not exist before their parents
        for n, sub_section in enumerate(sections[i:]):
            # if we reach the same heading level (which is not the original one), we are done
            if n != 0 and sub_section["level"] <= initial_level:
                break

            current_section.append(sub_section)

        joined_sections = [
            s["result"] for s in current_section if s["result"] is not None
        ]
        chunked_markdown.append("\n\n".join(joined_sections))

    return chunked_markdown


def chunk_markdown_by_list(markdown: str) -> list[str]:
    """
    Return a list of all lists, tasks, todos with its main heading
    """

    lines = markdown.splitlines()
    markdown_lists: list[str] = []
    current: list[str] | None = None
    current_heading: str = ""

    # build a list with all direct data of the given sections (meaning parent headings have no child content)
    for line in lines:
        # match `- [ ]` or `- [x]` or `- [/]` or `- `
        match = re.match(r"^- (\[[xX/ ]\] )?(.+)", line)
        if match:
            if current:
                markdown_lists.append("\n".join(current))

            current = [current_heading, line]
        else:
            # update the current heading to add as information
            if re.match(r"^(#{1,6}) (.+)", line):
                current_heading = line + "\n"
                continue

            # only add when its some sub list item, meaning it has at least one space
            match = re.match(r"\s+- (\[[xX/ ]\] )?(.+)", line)
            if current and match:
                current.append(line)

    # add the last list
    if current:
        markdown_lists.append("\n".join(current))

    return [list.strip() for list in markdown_lists]
