import subprocess
import sys
from pathlib import Path


def run(*args, input_text=None):
    return subprocess.run(
        [sys.executable, "-m", "main", *args],
        capture_output=True,
        text=True,
        input=input_text,
        cwd=Path(__file__).parent.parent,
    )


def test_basic_prompt():
    result = run("In order to succeed, make use of all tools.")
    assert result.returncode == 0
    assert "TokenWise Report" in result.stdout


def test_no_report_flag():
    result = run("--no-report", "In order to succeed.")
    assert result.returncode == 0
    assert "TokenWise" not in result.stdout
    assert len(result.stdout.strip()) > 0


def test_conservative_flag():
    result = run("--conservative", "In order to achieve best results, make use of resources.")
    assert result.returncode == 0
    assert "TokenWise Report" in result.stdout


def test_conservative_skips_stopword_removal():
    result = run("--conservative", "--no-report", "In order to achieve best results.")
    assert result.returncode == 0
    # conservative mode keeps stopwords — "to" and "best" should survive
    assert "best" in result.stdout


def test_output_flag(tmp_path):
    out_file = tmp_path / "output.txt"
    result = run("--output", str(out_file), "--no-report", "In order to succeed.")
    assert result.returncode == 0
    assert out_file.exists()
    assert len(out_file.read_text().strip()) > 0


def test_output_flag_writes_optimized_text(tmp_path):
    out_file = tmp_path / "output.txt"
    run("--output", str(out_file), "--no-report", "In order to succeed, make use of all tools.")
    content = out_file.read_text().strip()
    assert "in order to" not in content.lower()


def test_file_flag(tmp_path):
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("In order to succeed, make use of all tools.")
    result = run("--file", str(prompt_file))
    assert result.returncode == 0
    assert "TokenWise Report" in result.stdout


def test_missing_file_exits_with_error():
    result = run("--file", "/nonexistent/path/prompt.txt")
    assert result.returncode == 1
    assert "Error" in result.stdout
