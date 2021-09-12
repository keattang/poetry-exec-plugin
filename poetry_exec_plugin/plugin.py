import toml
import pathlib
import os

from cleo.helpers import argument
from cleo.application import Application

from poetry.console.commands.env_command import EnvCommand
from poetry.plugins.application_plugin import ApplicationPlugin

from simple_chalk import dim, red

from typing import Any


class ExecCommand(EnvCommand):

    name = "exec"
    description = "Execute a predefined command from your pyproject.toml"

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
        pyproject_foler_path = self.poetry.pyproject._file.path.parent
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
                red(
                    f"\nUnable to find the command '{cmd_name}'. To configure a command you must "
                    "add it to your pyproject.toml under the path "
                    "[tool.poetry-exec-plugin.commands]. For example:"
                    "\n\n"
                    "[tool.poetry-exec-plugin.commands]\n"
                    f'{cmd_name} = "echo Hello World"\n'
                )
            )
            return 1

        full_cmd = f"{cmd} {' '.join(self.argument('arguments'))}"
        shell = os.environ.get("SHELL", "/bin/sh")

        # Change directory to the folder that contains the pyproject.toml so that the command runs
        # from that folder (even if you call poetry exec from a subfolder). This mimics the
        # behaviour of npm/yarn.
        os.chdir(pyproject_foler_path)

        self.line(dim(f"Exec: {full_cmd}\n"))
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
