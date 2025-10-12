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
- a note that spans
  multiple lines
  that continue
      even with incorrect indentation

  or empty lines
- continue list also works as expected
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

result_5 = """
## private

- a note that spans
  multiple lines
  that continue
      even with incorrect indentation
  or empty lines
""".strip()


result_6 = """
## private

- continue list also works as expected
""".strip()


def test_list_chunks():
    result = chunk_markdown_by_list(example_markdown)

    assert result[0] == result_1
    assert result[1] == result_2
    assert result[2] == result_3
    assert result[3] == result_4
    assert result[4] == result_5
    assert result[5] == result_6


def test_list_chunks_with_quotes():
    markdown_with_quotes = """
# Example

## Sub Example

- a normal list
  - with a sub list
- then another list
  > with a quote itself
  - and a sub list
    > that has
    > multiline quotes
- a normal list
  - with a sub list
""".strip()

    normal_list = """
## Sub Example

- a normal list
  - with a sub list""".strip()

    quote_example = """
## Sub Example

- then another list
  > with a quote itself
  - and a sub list
    > that has
    > multiline quotes""".strip()

    result = chunk_markdown_by_list(markdown_with_quotes)

    assert len(result) == 3
    assert result[0] == normal_list
    assert result[1] == quote_example
    assert result[2] == normal_list


def test_list_chunks_with_fenced_code_blocks():
    markdown_with_code = """
# Example

## Sub Example

- item 1
- item 2
  - item 2.1
    > item 2.1.1
  - item 2.2

    ```example
    line 1
    line 2
    ```

- item 3
""".strip()

    start_list = """
## Sub Example

- item 1""".strip()

    code_list = """
## Sub Example

- item 2
  - item 2.1
    > item 2.1.1
  - item 2.2
    ```example
    line 1
    line 2
    ```""".strip()

    end_list = """
## Sub Example

- item 3""".strip()

    result = chunk_markdown_by_list(markdown_with_code)

    assert len(result) == 3
    assert result[0] == start_list
    assert result[1] == code_list
    assert result[2] == end_list
