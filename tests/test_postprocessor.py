from optimizer.postprocessor import (
    fix_punctuation_spacing,
    fix_capitalization,
    fix_apostrophes,
    postprocess,
)


def test_removes_space_before_comma():
    assert fix_punctuation_spacing("hello , world") == "hello, world"


def test_removes_space_before_period():
    assert fix_punctuation_spacing("hello .") == "hello."


def test_removes_space_before_question():
    assert fix_punctuation_spacing("today ?") == "today?"


def test_removes_space_before_exclamation():
    assert fix_punctuation_spacing("world !") == "world!"


def test_ensures_space_after_period():
    assert fix_punctuation_spacing("end.next") == "end. next"


def test_capitalizes_first_letter():
    assert fix_capitalization("hello world") == "Hello world"


def test_capitalizes_after_period():
    result = fix_capitalization("first sentence. second sentence.")
    assert result == "First sentence. Second sentence."


def test_capitalizes_after_exclamation():
    result = fix_capitalization("hello world! how are you?")
    assert result == "Hello world! How are you?"


def test_fix_apostrophe_negation():
    assert fix_apostrophes("do n't") == "don't"


def test_fix_apostrophe_possession():
    assert fix_apostrophes("user 's") == "user's"


def test_postprocess_full_pipeline():
    broken = "use feature , should help user . performance matters , system scale ."
    result = postprocess(broken)
    assert " ," not in result
    assert " ." not in result
    assert result[0].isupper()


def test_postprocess_empty_string():
    assert postprocess("") == ""


def test_postprocess_preserves_meaning():
    text = "hello world ! today ? fine , thank ."
    result = postprocess(text)
    assert "hello" in result.lower()
    assert "world" in result.lower()


def test_postprocess_real_output():
    from optimizer.core import Optimizer
    opt = Optimizer()
    result = opt.optimize(
        "In order to make use of this feature, please be advised that you should provide assistance to the user."
    )
    assert " ," not in result.optimized_text
    assert " ." not in result.optimized_text
    assert result.optimized_text[0].isupper()
