from markdown_chunker import chunk_markdown_by_list

example_markdown = """
# 2025-04-17 (Thursday)

## work

### repeating tasks

- [ ] open task
- [x] finished task
  - [/] cancelled task

### normal tasks

- note 1
  - note 1.1
    - note 1.1.1
  - note 1.2

## private

some irrelevant notes

- [/] private task 1
""".strip()

result_1 = """
### repeating tasks

- [ ] open task
""".strip()

result_2 = """
### repeating tasks

- [x] finished task
  - [/] cancelled task
""".strip()

result_3 = """
### normal tasks

- note 1
  - note 1.1
    - note 1.1.1
  - note 1.2
""".strip()

result_4 = """
## private

- [/] private task 1
""".strip()


def test_list_chunks():
    result = chunk_markdown_by_list(example_markdown)

    assert result[0] == result_1
    assert result[1] == result_2
    assert result[2] == result_3
    assert result[3] == result_4
