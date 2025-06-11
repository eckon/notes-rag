from markdown_chunker import chunk_markdown_by_heading

example_markdown = """
# 2025-04-17 (Thursday)

## work

### repeating tasks

- [x] test 1
- [x] test 2
  - [/] test 2.1
- [x] test 3

### normal tasks

- [x] task 1
- [x] task 2
  - [x] task 2.1
    - note 2.1.1
    - [x] task 2.1.2
  - note 2.2

## private

- [x] private task 1
""".strip()

example_markdown_work_section = """
## work

### repeating tasks

- [x] test 1
- [x] test 2
  - [/] test 2.1
- [x] test 3

### normal tasks

- [x] task 1
- [x] task 2
  - [x] task 2.1
    - note 2.1.1
    - [x] task 2.1.2
  - note 2.2
""".strip()

example_markdown_repeating_section = """
### repeating tasks

- [x] test 1
- [x] test 2
  - [/] test 2.1
- [x] test 3
""".strip()

example_markdown_normal_section = """
### normal tasks

- [x] task 1
- [x] task 2
  - [x] task 2.1
    - note 2.1.1
    - [x] task 2.1.2
  - note 2.2
""".strip()

example_markdown_private_section = """
## private

- [x] private task 1
""".strip()


def test_markdown_chunks():
    result = chunk_markdown_by_heading(example_markdown)

    assert result[0] == example_markdown
    assert result[1] == example_markdown_work_section
    assert result[2] == example_markdown_repeating_section
    assert result[3] == example_markdown_normal_section
    assert result[4] == example_markdown_private_section
