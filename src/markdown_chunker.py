from typing import List, Dict, Any
import re


def chunk_markdown_by_heading(markdown: str) -> List[str]:
    """
    Splits the given markdown string into sections based on headings.
    Each section is a string with the content of the section.

    Child sections are included in their parent section.
    """

    lines = markdown.splitlines()
    sections: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None

    # build a list with all direct data of the given sections (meaning parent headings have no child content)
    for line in lines:
        # match headings beginning with repeated `#`
        match = re.match(r"^(#{1,6}) (.+)", line)
        if match:
            if current:
                current["content"] = "\n".join(current["content"]).strip()
                sections.append(current)

            current = {
                "heading": match[2].strip(),
                "level": len(match[1]),
                "content": [line],
            }
        elif current:
            current["content"].append(line)

    # add the last section
    if current:
        current["content"] = "\n".join(current["content"]).strip()
        sections.append(current)

    # enhance lists, to let parents include their children, based on ordering
    chunked_markdown: List[str] = []
    for i, section in enumerate(sections):
        initial_level = section["level"]
        current_section: List[Dict[str, Any]] = []

        # only iterate over following sections, as children can not exist before their parents
        for n, sub_section in enumerate(sections[i:]):
            # if we reach the same heading level (which is not the original one), we are done
            if n != 0 and sub_section["level"] <= initial_level:
                break

            current_section.append(sub_section)

        chunked_markdown.append(
            ("\n".join(s["content"] + "\n" for s in current_section)).strip()
        )

    return chunked_markdown


def chunk_markdown_by_list(markdown: str) -> List[str]:
    """
    Return a list of all lists, tasks, todos with its main heading
    """

    lines = markdown.splitlines()
    markdown_lists: List[str] = []
    current: List[str] | None = None
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
