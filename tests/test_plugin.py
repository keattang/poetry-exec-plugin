from cleo.testers.command_tester import CommandTester
from cleo.application import Application

from poetry_exec_plugin.plugin import ExecCommand

from poetry.utils.env import MockEnv

from pathlib import Path


def test_execute() -> None:
    application = Application()
    command_instance = ExecCommand()
    command_instance.set_env(MockEnv(path=Path("/prefix"), base=Path("/base/prefix"), is_venv=True))
    application.add(command_instance)

    command = application.find("exec")
    command_tester = CommandTester(command)
    command_tester.execute("test-script")

    assert "Hello World" in command_tester.io.fetch_output()
