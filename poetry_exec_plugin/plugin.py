import os
import shlex
import sys

from cleo.helpers import argument
from cleo.application import Application

from poetry.console.commands.env_command import EnvCommand
from poetry.plugins.application_plugin import ApplicationPlugin

from typing import Any, List


def shlex_join(cmd_list: List[str]) -> str:
    if sys.version_info < (3, 8):
        # shlex.join has been introduced in Python 3.8
        # https://github.com/python/cpython/blob/3.9/Lib/shlex.py#L318
        return " ".join(shlex.quote(x) for x in cmd_list)
    else:
        return shlex.join(cmd_list)


class ExecCommand(EnvCommand):

    name = "exec"
    description = "Execute a predefined command from your pyproject.toml."

    arguments = [
        argument("cmd", "The command to run from your pyproject.toml.", multiple=False),
        argument(
            "arguments",
            "Additional arguments to append to the command.",
            multiple=True,
            optional=True,
        ),
    ]

    def handle(self) -> Any:
        pyproject_folder_path = self.poetry.pyproject._file.path.parent
        pyproject_data = self.poetry.pyproject.data

        cmd_name = self.argument("cmd")
        cmd = (
            pyproject_data.get("tool", {})
            .get("poetry-exec-plugin", {})
            .get("commands", {})
            .get(cmd_name)
        )

        if not cmd:
            self.line_error(
                f"\nUnable to find the command '{cmd_name}'. To configure a command you must "
                "add it to your pyproject.toml under the path "
                "[tool.poetry-exec-plugin.commands]. For example:"
                "\n\n"
                "[tool.poetry-exec-plugin.commands]\n"
                f'{cmd_name} = "echo Hello World"\n',
                style="error",
            )
            return 1

        full_cmd = f"{cmd} {shlex_join(self.argument('arguments'))}"
        shell = os.environ.get("SHELL", "/bin/sh")

        # Change directory to the folder that contains the pyproject.toml so that the command runs
        # from that folder (even if you call poetry exec from a subfolder). This mimics the
        # behaviour of npm/yarn.
        os.chdir(pyproject_folder_path)

        self.line(f"Exec: {full_cmd}\n", style="info")
        result = self.env.execute(*[shell, "-c", full_cmd])

        # NOTE: If running on mac or linux nothing will be executed after the previous line. This
        # is because poetry uses os.execvpe to run the command which means that the current process
        # is replaced by the command. If on windows it uses subprocess.run which means the code
        # after this comment will be executed.

        self.line("\n✨ Done!")

        if result:
            return result.returncode


def factory() -> ExecCommand:
    return ExecCommand()


class ExecPlugin(ApplicationPlugin):
    def activate(self, application: Application, *args: Any, **kwargs: Any) -> None:
        application.command_loader.register_factory("exec", factory)
