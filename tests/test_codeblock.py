from optimizer.codeblock import extract, restore
from optimizer.core import Optimizer


def test_extract_inline_backtick():
    text = "Use `calculate_sum(numbers)` to get the total."
    modified, blocks = extract(text)
    assert "`" not in modified
    assert len(blocks) == 1
    assert blocks[0] == "`calculate_sum(numbers)`"


def test_extract_fenced_block():
    text = "Run:\n```python\ndef hello():\n    print('hi')\n```\nDone."
    modified, blocks = extract(text)
    assert "```" not in modified
    assert len(blocks) == 1
    assert "def hello" in blocks[0]


def test_extract_multiple_blocks():
    text = "Use `foo()` and `bar()` together."
    modified, blocks = extract(text)
    assert len(blocks) == 2
    assert "`foo()`" in blocks
    assert "`bar()`" in blocks


def test_extract_fenced_before_inline():
    text = "Example:\n```\ncode block\n```\nand `inline` too."
    modified, blocks = extract(text)
    assert len(blocks) == 2


def test_restore_roundtrip():
    text = "Call `func(x)` and see ```\nresult\n``` here."
    modified, blocks = extract(text)
    restored = restore(modified, blocks)
    assert restored == text


def test_extract_no_code_returns_unchanged():
    text = "This is plain text with no code."
    modified, blocks = extract(text)
    assert modified == text
    assert blocks == []


def test_optimizer_preserves_inline_code():
    opt = Optimizer()
    text = "In order to make use of `requests.get(url)`, please handle errors."
    result = opt.optimize(text)
    assert "`requests.get(url)`" in result.optimized_text


def test_optimizer_preserves_fenced_block():
    opt = Optimizer()
    text = "Run this:\n```python\ndef hello():\n    print('Hello world')\n```"
    result = opt.optimize(text)
    assert "def hello():" in result.optimized_text
    assert "    print(" in result.optimized_text


def test_optimizer_preserves_indentation_in_code():
    opt = Optimizer()
    text = "Example:\n```\nif x:\n    return True\n```"
    result = opt.optimize(text)
    assert "    return True" in result.optimized_text


def test_optimizer_no_capitalization_inside_code():
    opt = Optimizer()
    text = "Use `requests.get(url)` to fetch data."
    result = opt.optimize(text)
    # postprocessor must NOT capitalize 'get' after the dot inside backticks
    assert "`requests.get(url)`" in result.optimized_text


def test_optimizer_still_optimizes_surrounding_text():
    opt = Optimizer()
    text = "In order to make use of `func()`, please be advised that you should handle the errors."
    result = opt.optimize(text)
    assert result.tokens_saved > 0
    assert "`func()`" in result.optimized_text
