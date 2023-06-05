import pathlib
import shutil
import subprocess
from typing import Optional

import pytest


def minimal_pyproject_template(commands_section: str, config_section: Optional[str] = None) -> str:
    result = f"""[tool.poetry]
name = "foo"
version = "1.0.0"
description = "Foo"
authors = ["bar"]

[tool.poetry-exec-plugin.commands]
{commands_section}
"""
    if config_section is not None:
        result += f"[tool.poetry-exec-plugin.config]\n{config_section}\n"
    return result


def test_execute(tmp_path: pathlib.Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        minimal_pyproject_template("test-script = 'echo Hello World'"),
    )
    proc = subprocess.Popen(
        ["poetry", "exec", "test-script"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=tmp_path,
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
    proc = subprocess.Popen(
        ["poetry", "exec", "test-script", "Hello World\n"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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
        cwd=tmp_path,
    )
    out, err = proc.communicate()
    assert b"Exec: printf 'Hello World\n'" in out
    assert b"\nHello World\n" in out
    assert err == b""
    assert proc.returncode == 0


@pytest.mark.skipif(
    shutil.which("printf") is None,
    reason="printf binary is not available",
)
@pytest.mark.parametrize(
    "resolve_poetry_exec",
    (True, False),
    ids=("resolve-poetry-exec=true", "resolve-poetry-exec=false"),
)
def test_config_resolve_poetry_exec(tmp_path: pathlib.Path, resolve_poetry_exec: bool) -> None:
    commands_section = """print = "printf"
"hello:poetry" = "poetry exec print 'Hello ' && poetry exec print 'World'"
"hello:raw" = "printf 'Hello ' && printf 'World'"
"""
    expected_output_enabled = b"Hello World"
    config_section: Optional[str] = None
    if resolve_poetry_exec:
        config_section = "resolve-poetry-exec = true\n"
        expected_output = expected_output_enabled
    else:
        expected_output = b"poetry exec print 'Hello ' && poetry exec print 'World'"

    pyproject_toml = minimal_pyproject_template(
        commands_section,
        config_section=config_section,
    )
    (tmp_path / "pyproject.toml").write_text(pyproject_toml)

    proc = subprocess.Popen(
        ["poetry", "exec", "hello:poetry"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=tmp_path,
    )
    out, err = proc.communicate()
    assert expected_output in out
    if resolve_poetry_exec:
        assert b"poetry" not in out
        assert b"exec" not in out
    else:
        assert b"poetry" in out
        assert b"exec" in out
    assert err == b""
    assert proc.returncode == 0

    proc = subprocess.Popen(
        ["poetry", "exec", "hello:raw"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=tmp_path,
    )
    out, err = proc.communicate()
    assert expected_output_enabled in out
    assert b"poetry" not in out
    assert b"exec" not in out
    assert err == b""
    assert proc.returncode == 0
