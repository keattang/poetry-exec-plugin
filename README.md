# poetry-exec-plugin

A plugin for poetry that allows you to execute scripts defined in your pyproject.toml, just like you can in npm or pipenv

## Installation

Installation requires poetry 1.2.0+. To install this plugin run:

`poetry self add poetry-exec-plugin`

For other methods of installing plugins see the [poetry documentation](https://python-poetry.org/docs/master/plugins/#the-plugin-add-command).

## Usage

To use this plugin, first define the scripts that you wish to be able to execute in your `pyproject.toml` file under a section called `tool.poetry-exec-plugin.commands`. For example:

```toml
[tool.poetry-exec-plugin.commands]
hello-world = "TEXT=hello-world; echo $TEXT"
lint = "flake8"
```

This will define a script that you can then execute with the `poetry exec <script>` command. This will execute your script inside of the environment that poetry creates for you, allowing you to access the dependencies installed for your project. The script will also always run from the same directory as your `pyproject.toml` file. This mimics the behaviour of npm/yarn. For example:

```bash
$ poetry exec hello-world
hello-world

$ poetry exec lint
./my_file.py:29:25: E222 multiple spaces after operator
```

Anything that you append to your exec command will be appended to the script. You can use this to pass extra flags and arguments to the commands in your scripts. For example:

```bash
$ poetry exec hello-world one two three
hello-world one two three

$ poetry exec lint --version
3.9.2 (mccabe: 0.6.1, pycodestyle: 2.7.0, pyflakes: 2.3.1) CPython 3.9.0 on Darwin
```

### Configuration

You can configure the execution of the plugin at `tool.poetry-exec-plugin.config` in your *pyproject.toml* file.

```toml
[tool.poetry-exec-plugin.config]
resolve-poetry-exec = true
```

The supported configuration fields are:

- <a href="#config_resolve-poetry-exec">#</a> **resolve-poetry-exec** (*boolean*) ⇒ If enabled, when you call a command from another command, the `poetry exec <command>` invocation will be replaced by the final command speeding up the execution. By default is `false`.

## Publishing

To publish a new version,first bump the package version in `pyproject.toml` and commit your changes to the `main` branch (via pull request). Then in GitHub create a new release with the new version as the tag and name. You can use the handy auto release notes feature to populate the release description.
