import os
import shlex
import sys
from typing import Any, List, Dict

from cleo.application import Application
from cleo.helpers import argument
from poetry.console.commands.env_command import EnvCommand
from poetry.plugins.application_plugin import ApplicationPlugin


def shlex_join(cmd_list: List[str]) -> str:
    if sys.version_info < (3, 8):
        # shlex.join has been introduced in Python 3.8
        # https://github.com/python/cpython/blob/3.9/Lib/shlex.py#L318
        return " ".join(shlex.quote(x) for x in cmd_list)
    else:
        return shlex.join(cmd_list)


def resolve_poetry_exec_calls(cmd: str, commands: Dict[str, str]) -> str:
    """Replace internal `poetry exec` calls with the correspondent commands.

    Builds a new command string from the given one replacing `poetry exec <foo>`
    calls with the commands defined in the configuration. This avoids to call
    `poetry` when reusing commands from other ones.
    """
    clean_cmd, i = "", 0
    split_cmd = list(shlex.shlex(cmd, posix=True, punctuation_chars=True))
    split_length = len(split_cmd)
    while i < split_length:
        arg = split_cmd[i]
        if (
            i < split_length - 2
            and arg == "poetry"
            and split_cmd[i + 1] == "exec"
            and split_cmd[i + 2] in commands
        ):
            clean_cmd += f" {commands[split_cmd[i + 2]]}"
            i += 3
        else:
            if " " in arg:
                arg = "'" + arg.replace("'", "\\'") + "'"
            clean_cmd += f" {arg}"
            i += 1
    return clean_cmd.lstrip()


class ExecCommand(EnvCommand):
    name = "exec"
    description = "Execute a predefined command from your pyproject.toml."

    arguments = [
        argument(
            "cmd", "The command to run from your pyproject.toml.", multiple=False
        ),
        argument(
            "arguments",
            "Additional arguments to append to the command.",
            multiple=True,
            optional=True,
        ),
    ]

    def handle(self) -> Any:
        pyproject_folder_path = self.poetry.pyproject.file.path.parent
        pyproject_data = self.poetry.pyproject.data

        cmd_name = self.argument("cmd")
        pyproject_object = pyproject_data.get("tool", {}).get("poetry-exec-plugin", {})
        commands = pyproject_object.get("commands", {})
        cmd = commands.get(cmd_name)

        if not cmd:
            self.line_error(
                f"\nUnable to find the command '{cmd_name}'. To configure a command "
                "you must add it to your pyproject.toml under the path "
                "[tool.poetry-exec-plugin.commands]. For example:"
                "\n\n"
                "[tool.poetry-exec-plugin.commands]\n"
                f'{cmd_name} = "echo Hello World"\n',
                style="error",
            )
            return 1

        config = pyproject_object.get("config", {})

        if config.get("resolve-poetry-exec"):
            resolved_cmd = resolve_poetry_exec_calls(cmd, commands)
        else:
            resolved_cmd = cmd
        full_cmd = f"{resolved_cmd} {shlex_join(self.argument('arguments'))}"
        shell = os.environ.get("SHELL", "/bin/sh")

        # Change directory to the folder that contains the pyproject.toml so that
        # the command runs from that folder (even if you call poetry exec from a
        # subfolder). This mimics the behaviour of npm/yarn.
        os.chdir(pyproject_folder_path)

        self.line(f"Exec: {full_cmd}\n", style="info")
        result = self.env.execute(*[shell, "-c", full_cmd])

        # NOTE: If running on mac or linux nothing will be executed after the
        # previous line. This is because poetry uses os.execvpe to run the command
        # which means that the current process is replaced by the command. If on
        # windows it uses subprocess.run which means the code after this comment
        # will be executed.

        self.line("\n✨ Done!")

        if result:
            return result.returncode


def factory() -> ExecCommand:
    return ExecCommand()


class ExecPlugin(ApplicationPlugin):
    def activate(self, application: Application, *args: Any, **kwargs: Any) -> None:
        application.command_loader.register_factory("exec", factory)
