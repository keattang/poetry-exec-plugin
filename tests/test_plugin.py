import os
import pathlib
import subprocess


def minimal_pyproject_template(commands_section: str) -> str:
    return f"""[tool.poetry]
name = "foo"
version = "1.0.0"
description = "Foo"
authors = ["bar"]

[tool.poetry-exec-plugin.commands]
{commands_section}
"""


def test_execute(tmp_path: pathlib.Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        minimal_pyproject_template("test-script = 'echo Hello World'"),
    )
    os.chdir(tmp_path)

    proc = subprocess.Popen(
        ["poetry", "exec", "test-script"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )
    out, err = proc.communicate()
    assert b"Exec: echo Hello World" in out
    assert b"\nHello World\n" in out
    assert err == b""
    assert proc.returncode == 0


def test_arguments_propagation(tmp_path: pathlib.Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        minimal_pyproject_template("test-script = 'printf'"),
    )
    os.chdir(tmp_path)
    proc = subprocess.Popen(
        ["poetry", "exec", "test-script", "Hello World\n"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )
    out, err = proc.communicate()
    assert b"Exec: printf 'Hello World\n'" in out
    assert b"\nHello World\n" in out
    assert err == b""
    assert proc.returncode == 0


def test_arguments_propagation_with_double_dash(tmp_path: pathlib.Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        minimal_pyproject_template("test-script = 'printf'"),
    )
    os.chdir(tmp_path)
    proc = subprocess.Popen(
        ["poetry", "exec", "test-script", "--", "Hello World\n"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )
    out, err = proc.communicate()
    assert b"Exec: printf 'Hello World\n'" in out
    assert b"\nHello World\n" in out
    assert err == b""
    assert proc.returncode == 0
