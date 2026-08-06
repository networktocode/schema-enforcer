"""Tasks for use with Invoke."""

import os
<<<<<<< HEAD
import sys
from invoke import task

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        sys.exit("Please make sure to `pip install tomli` or enable the Poetry shell and run `poetry install`.")


def project_ver():
    """Find version from pyproject.toml to use for docker image tagging."""
    with open("pyproject.toml", "rb") as config_file:
        return tomllib.load(config_file)["tool"]["poetry"].get("version", "latest")
=======
import re
from pathlib import Path

from invoke import Collection, Exit
from invoke import task as invoke_task
>>>>>>> 31cc3ca (Cookie initially baked targeting develop by NetworkToCode Cookie Drift Manager Tool)


def is_truthy(arg):
    """Convert "truthy" strings into Booleans.

    Examples:
        >>> is_truthy('yes')
        True
<<<<<<< HEAD

=======
>>>>>>> 31cc3ca (Cookie initially baked targeting develop by NetworkToCode Cookie Drift Manager Tool)
    Args:
        arg (str): Truthy string (True values are y, yes, t, true, on and 1; false values are n, no,
        f, false, off and 0. Raises ValueError if val is anything else.
    """
    if isinstance(arg, bool):
        return arg

    val = str(arg).lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
<<<<<<< HEAD
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError(f"Invalid truthy value: `{arg}`")


with open("pyproject.toml", "rb") as config_file:
    PYPROJECT_CONFIG = tomllib.load(config_file)
TOOL_CONFIG = PYPROJECT_CONFIG["tool"]["poetry"]

# Can be set to a separate Python version to be used for launching or building image
PYTHON_VER = os.getenv("PYTHON_VER", "3.10")
# Can be set to a separate ANsible version to be used for launching or building image
ANSIBLE_VER = os.getenv("ANSIBLE_VER", "2.16.14")
ANSIBLE_PACKAGE = os.getenv("ANSIBLE_PACKAGE", "ansible-core")
# Name of the docker image/image
IMAGE_NAME = os.getenv("IMAGE_NAME", TOOL_CONFIG["name"])
# Tag for the image
IMAGE_VER = os.getenv("IMAGE_VER", f"{TOOL_CONFIG['version']}-py{PYTHON_VER}")
# Gather current working directory for Docker commands
PWD = os.getcwd()
# Local or Docker execution provide "local" to run locally without docker execution
INVOKE_LOCAL = is_truthy(os.getenv("INVOKE_LOCAL", False))  # pylint: disable=W1508


def _get_image_name(with_ansible=False):
    """Gets the name of the container image to use.

    Args:
        with_ansible (bool): Get name of container image with Ansible installed.

    Returns:
        str: Name of container image. Includes tag.
    """
    if with_ansible and not os.getenv("GITHUB_ACTION", None):
        name = f"{IMAGE_NAME}:{IMAGE_VER}-{ANSIBLE_PACKAGE}{ANSIBLE_VER}"
    else:
        name = f"{IMAGE_NAME}:{IMAGE_VER}"

    return name


def run_cmd(context, exec_cmd, with_ansible=False):
    """Wrapper to run the invoke task commands.

    Args:
        context (invoke.task): Invoke task object.
        exec_cmd (str): Command to run.
        with_ansible (bool): Whether to run the command in a container that has ansible installed
=======
    if val in ("n", "no", "f", "false", "off", "0"):
        return False
    raise ValueError(f"Invalid truthy value: `{arg}`")


# Use pyinvoke configuration for default values, see http://docs.pyinvoke.org/en/stable/concepts/configuration.html
# Variables may be overwritten in invoke.yml or by the environment variables INVOKE_SCHEMA-ENFORCER_xxx
namespace = Collection("schema_enforcer")
namespace.configure(
    {
        "schema_enforcer": {
            "project_name": "schema_enforcer",
            "python_ver": "3.10",
            "local": is_truthy(os.getenv("INVOKE_SCHEMA-ENFORCER_LOCAL", "false")),
            "image_name": "schema_enforcer",
            "image_ver": os.getenv("INVOKE_SCHEMA-ENFORCER_IMAGE_VER", "latest"),
            "pwd": Path(__file__).parent,
        }
    }
)


# pylint: disable=keyword-arg-before-vararg
def task(function=None, *args, **kwargs):
    """Task decorator to override the default Invoke task decorator and add each task to the invoke namespace."""

    def task_wrapper(function=None):
        """Wrapper around invoke.task to add the task to the namespace as well."""
        if args or kwargs:
            task_func = invoke_task(*args, **kwargs)(function)
        else:
            task_func = invoke_task(function)
        namespace.add_task(task_func)
        return task_func

    if function:
        # The decorator was called with no arguments
        return task_wrapper(function)
    # The decorator was called with arguments
    return task_wrapper


def run_command(context, exec_cmd, port=None, rm=True):
    """Wrapper to run the invoke task commands.

    Args:
        context ([invoke.task]): Invoke task object.
        exec_cmd ([str]): Command to run.
        port (int): Used to serve local docs.
        rm (bool): Whether to remove the container after running the command.
>>>>>>> 31cc3ca (Cookie initially baked targeting develop by NetworkToCode Cookie Drift Manager Tool)

    Returns:
        result (obj): Contains Invoke result from running task.
    """
<<<<<<< HEAD
    name = _get_image_name(with_ansible)

    if INVOKE_LOCAL:
        print(f"LOCAL - Running command {exec_cmd}")
        result = context.run(exec_cmd, pty=True)
    else:
        print(f"DOCKER - Running command: {exec_cmd} container: {name}")
        result = context.run(f"docker run -it -v {PWD}:/local {name} sh -c '{exec_cmd}'", pty=True)
=======
    if is_truthy(context.schema_enforcer.local):
        print(f"LOCAL - Running command {exec_cmd}")
        result = context.run(exec_cmd, pty=True)
    else:
        print(
            f"DOCKER - Running command: {exec_cmd} container: {context.schema_enforcer.image_name}:{context.schema_enforcer.image_ver}"
        )
        if port:
            result = context.run(
                f"docker run -it {'--rm' if rm else ''} -p {port} -v {context.schema_enforcer.pwd}:/local {context.schema_enforcer.image_name}:{context.schema_enforcer.image_ver} sh -c '{exec_cmd}'",
                pty=True,
            )
        else:
            result = context.run(
                f"docker run -it {'--rm' if rm else ''} -v {context.schema_enforcer.pwd}:/local {context.schema_enforcer.image_name}:{context.schema_enforcer.image_ver} sh -c '{exec_cmd}'",
                pty=True,
            )
>>>>>>> 31cc3ca (Cookie initially baked targeting develop by NetworkToCode Cookie Drift Manager Tool)

    return result


<<<<<<< HEAD
@task
def build_image(
    context, cache=True, force_rm=False, hide=False, with_ansible=False
):  # pylint: disable=too-many-arguments
    """Builds a container with schema-enforcer installed.

    Args:
        context (invoke.task): Invoke task object
        cache (bool): Do not use cache when building the image
        force_rm (bool): Always remove intermediate containers
        hide: (bool): Suppress output from docker build
        with_ansible (bool): Build a container with Ansible installed
    """
    name = _get_image_name(with_ansible)
    env = {"PYTHON_VER": PYTHON_VER}

    if with_ansible:
        env["ANSIBLE_VER"] = ANSIBLE_VER
        env["ANSIBLE_PACKAGE"] = ANSIBLE_PACKAGE
        command = f"docker build --tag {name} --target with_ansible"
        command += f" --build-arg ANSIBLE_VER={ANSIBLE_VER} --build-arg ANSIBLE_PACKAGE={ANSIBLE_PACKAGE}"

    else:
        command = command = f"docker build --tag {name} --target base"

    command += f" --build-arg PYTHON_VER={PYTHON_VER} -f Dockerfile ."
    if not cache:
        command += " --no-cache"
    if force_rm:
        command += " --force-rm"

    print(f"Building image {name}")
    result = context.run(command, hide=hide, env=env)

    if result.exited != 0:
        print(f"Failed to build image {name}\nError: {result.stderr}")


@task
def clean_image(context, with_ansible=False):
    """Remove the schema-enforcer container.

    Args:
        context (obj): Used to run specific commands
        with_ansible (bool): Remove schema-enforcer container with ansible installed
    """
    name = _get_image_name(with_ansible)
    print(f"Attempting to forcefully remove image {name}")
    context.run(f"docker rmi {name} --force")


=======
# ------------------------------------------------------------------------------
# BUILD
# ------------------------------------------------------------------------------
>>>>>>> 31cc3ca (Cookie initially baked targeting develop by NetworkToCode Cookie Drift Manager Tool)
@task(
    help={
        "cache": "Whether to use Docker's cache when building images (default enabled)",
        "force_rm": "Always remove intermediate images",
        "hide": "Suppress output from Docker",
    }
)
def build(context, cache=True, force_rm=False, hide=False):
<<<<<<< HEAD
    """This will build an image with the provided name and python version.

    Args:
        context (obj): Used to run specific commands
        cache (bool): Do not use cache when building the image
        force_rm (bool): Always remove intermediate containers
        hide (bool): Suppress output from docker build
    """
    build_image(context, cache, force_rm, hide=hide)
    build_image(context, cache, force_rm, hide=hide, with_ansible=True)
=======
    """Build a Docker image."""
    print(f"Building image {context.schema_enforcer.image_name}:{context.schema_enforcer.image_ver}")
    command = f"docker build --tag {context.schema_enforcer.image_name}:{context.schema_enforcer.image_ver} --build-arg PYTHON_VER={context.schema_enforcer.python_ver} -f Dockerfile ."

    if not cache:
        command += " --no-cache"
    if force_rm:
        command += " --force-rm"

    result = context.run(command, hide=hide)
    if result.exited != 0:
        print(
            f"Failed to build image {context.schema_enforcer.image_name}:{context.schema_enforcer.image_ver}\nError: {result.stderr}"
        )


@task
def generate_packages(context):
    """Generate all Python packages inside docker and copy the file locally under dist/."""
    command = "poetry build"
    run_command(context, command)


@task(
    help={
        "check": (
            "If enabled, check for outdated dependencies in the poetry.lock file, "
            "instead of generating a new one. (default: disabled)"
        )
    }
)
def lock(context, check=False):
    """Generate poetry.lock inside the library container."""
    run_command(context, f"poetry {'check' if check else 'lock --no-update'}")
>>>>>>> 31cc3ca (Cookie initially baked targeting develop by NetworkToCode Cookie Drift Manager Tool)


@task
def clean(context):
<<<<<<< HEAD
    """This will remove a specific image.

    Args:
        context (obj): Used to run specific commands
    """
    clean_image(context)
    clean_image(context, with_ansible=True)


@task
def rebuild(context, cache=True, force_rm=False):
    """This will clean the image and then rebuild image without using cache.

    Args:
        context (obj): Used to run specific commands
        cache (bool): Use cache for rebuild
        force_rm (bool): Always remove intermediate containers
    """
    clean(context)
    build(context, cache=cache, force_rm=force_rm)


@task
def pytest(context):
    """This will run pytest for the specified name and Python version.

    Args:
        context (obj): Used to run specific commands
    """
    exec_cmd = 'find tests/ -name "test_*.py" -a -not -name "test_cli_ansible_not_exists.py" | xargs pytest -vv'
    run_cmd(context, exec_cmd, with_ansible=True)


@task
def pytest_without_ansible(context):
    """This will run pytest only to assert the correct errors are raised when pytest is not installed.

    This must be run inside of a container or environment in which ansible is not installed, otherwise the test case
    assertion will fail.

    Args:
        context (obj): Used to run specific commands
    """
    exec_cmd = 'find tests/ -name "test_cli_ansible_not_exists.py" | xargs pytest -vv'
    run_cmd(context, exec_cmd)


@task
def black(context):
    """This will run black to check that Python files adherence to black standards.

    Args:
        context (obj): Used to run specific commands
    """
    exec_cmd = "black --check --diff ."
    run_cmd(context, exec_cmd, with_ansible=True)


@task
def flake8(context):
    """This will run flake8 for the specified name and Python version.

    Args:
        context (obj): Used to run specific commands
    """
    exec_cmd = "flake8 ."
    run_cmd(context, exec_cmd, with_ansible=True)
=======
    """Remove the project specific image."""
    print(
        f"Attempting to forcefully remove image {context.schema_enforcer.image_name}:{context.schema_enforcer.image_ver}"
    )
    context.run(f"docker rmi {context.schema_enforcer.image_name}:{context.schema_enforcer.image_ver} --force")
    print(f"Successfully removed image {context.schema_enforcer.image_name}:{context.schema_enforcer.image_ver}")


@task
def rebuild(context):
    """Clean the Docker image and then rebuild without using cache."""
    clean(context)
    build(context, cache=False)


@task
def coverage(context):
    """Run the coverage report against pytest."""
    exec_cmd = "coverage run --source=schema_enforcer -m pytest"
    run_command(context, exec_cmd)
    run_command(context, "coverage report")
    run_command(context, "coverage html")


@task(
    help={
        "pattern": "Only run tests which match the given substring. Can be used multiple times.",
        "label": "Module path to run (e.g., tests/unit/test_foo.py). Can be used multiple times.",
    },
    iterable=["pattern", "label"],
)
def pytest(context, pattern=None, label=None):
    """Run pytest test cases."""
    exec_cmd = "pytest -vv --doctest-modules schema_enforcer/ && coverage run --source=schema_enforcer -m pytest && coverage report"
    run_command(context, exec_cmd)

    doc_test_cmd = "pytest -vv --doctest-modules schema_enforcer/"
    pytest_cmd = "coverage run --source=schema_enforcer -m pytest"
    if pattern:
        pytest_cmd += "".join([f" -k {_pattern}" for _pattern in pattern])
    if label:
        pytest_cmd += "".join([f" {_label}" for _label in label])
    coverage_cmd = "coverage report"
    exec_cmd = " && ".join([doc_test_cmd, pytest_cmd, coverage_cmd])
    run_command(context, exec_cmd)


@task(aliases=("a",))
def autoformat(context):
    """Run code autoformatting."""
    ruff(context, action=["format"], fix=True)


@task(
    help={
        "action": "Available values are `['lint', 'format']`. Can be used multiple times. (default: `['lint', 'format']`)",
        "target": "File or directory to inspect, repeatable (default: all files in the project will be inspected)",
        "fix": "Automatically fix selected actions. May not be able to fix all issues found. (default: False)",
        "output_format": "See https://docs.astral.sh/ruff/settings/#output-format for details. (default: `concise`)",
    },
    iterable=["action", "target"],
)
def ruff(context, action=None, target=None, fix=False, output_format="concise"):
    """Run ruff to perform code formatting and/or linting."""
    if not action:
        action = ["lint", "format"]
    if not target:
        target = ["."]

    exit_code = 0

    if "format" in action:
        command = "ruff format "
        if not fix:
            command += "--check "
        command += " ".join(target)
        if not run_command(context, command):
            exit_code = 1

    if "lint" in action:
        command = "ruff check "
        if fix:
            command += "--fix "
        command += f"--output-format {output_format} "
        command += " ".join(target)
        if not run_command(context, command):
            exit_code = 1

    if exit_code != 0:
        raise Exit(code=exit_code)
>>>>>>> 31cc3ca (Cookie initially baked targeting develop by NetworkToCode Cookie Drift Manager Tool)


@task
def pylint(context):
<<<<<<< HEAD
    """This will run pylint for the specified name and Python version.
=======
    """Run pylint for the specified name and Python version.
>>>>>>> 31cc3ca (Cookie initially baked targeting develop by NetworkToCode Cookie Drift Manager Tool)

    Args:
        context (obj): Used to run specific commands
    """
<<<<<<< HEAD
    exec_cmd = "pylint **/*.py"
    run_cmd(context, exec_cmd, with_ansible=True)
=======
    exec_cmd = 'find . -name "*.py" | grep -vE "tests/unit" | xargs pylint'
    run_command(context, exec_cmd)
>>>>>>> 31cc3ca (Cookie initially baked targeting develop by NetworkToCode Cookie Drift Manager Tool)


@task
def yamllint(context):
<<<<<<< HEAD
    """This will run yamllint to validate formatting adheres to NTC defined YAML standards.

    Args:
        context (obj): Used to run specific commands
        name (str): Used to name the docker image
        image_ver (str): Define image version
        local (bool): Define as `True` to execute locally
    """
    exec_cmd = "yamllint ."
    run_cmd(context, exec_cmd, with_ansible=True)


@task
def pydocstyle(context):
    """This will run pydocstyle to validate docstring formatting adheres to NTC defined standards.
=======
    """Run yamllint to validate formatting adheres to NTC defined YAML standards.

    Args:
        context (obj): Used to run specific commands
    """
    exec_cmd = "yamllint ."
    run_command(context, exec_cmd)


@task
def cli(context):
    """Enter the image to perform troubleshooting or dev work.
>>>>>>> 31cc3ca (Cookie initially baked targeting develop by NetworkToCode Cookie Drift Manager Tool)

    Args:
        context (obj): Used to run specific commands
    """
<<<<<<< HEAD
    exec_cmd = "pydocstyle ."
    run_cmd(context, exec_cmd, with_ansible=True)


@task
def bandit(context):
    """This will run bandit to validate basic static code security analysis.

    Args:
        context (obj): Used to run specific commands
    """
    exec_cmd = "bandit --recursive ./ --configfile .bandit.yml"
    run_cmd(context, exec_cmd, with_ansible=True)


@task
def tests(context):
    """This will run all tests for the specified name and Python version.

    Args:
        context (obj): Used to run specific commands
    """
    black(context)
    flake8(context)
    pylint(context)
    yamllint(context)
    pydocstyle(context)
    bandit(context)
    pytest(context)
    pytest_without_ansible(context)
=======
    dev = f"docker run -it -v {context.schema_enforcer.pwd}:/local {context.schema_enforcer.image_name}:{context.schema_enforcer.image_ver} /bin/bash"
    context.run(f"{dev}", pty=True)


@task(
    help={
        "lint-only": "Only run linters; unit tests will be excluded. (default: False)",
    }
)
def tests(context, lint_only=False):
    """Run all tests for the specified name and Python version.

    Args:
        context (obj): Used to run specific commands
        lint_only (bool): If True, only run linters and skip unit tests.
    """
    # If we are not running locally, start the docker containers so we don't have to for each test
    # Sorted loosely from fastest to slowest
    print("Running ruff...")
    ruff(context)
    print("Running yamllint...")
    yamllint(context)
    print("Running poetry check...")
    lock(context, check=True)
    print("Running pylint...")
    pylint(context)
    print("Running mkdocs...")
    build_and_check_docs(context)
    if not lint_only:
        print("Running unit tests...")
        pytest(context)
>>>>>>> 31cc3ca (Cookie initially baked targeting develop by NetworkToCode Cookie Drift Manager Tool)
    print("All tests have passed!")


@task
<<<<<<< HEAD
def cli(context, with_ansible=False):
    """This will enter the image to perform troubleshooting or dev work.

    Args:
        context (obj): Used to run specific commands
        with_ansible (str): Attach to container with ansible version specified by the 'ANSIBLE_VER' env var
    """
    name = _get_image_name(with_ansible)
    dev = f"docker run -it -v {PWD}:/local {name} /bin/bash"
    context.run(f"{dev}", pty=True)
=======
def build_and_check_docs(context):
    """Build documentation and test the configuration."""
    command = "mkdocs build --no-directory-urls --strict"
    run_command(context, command)

    # Check for the existence of a release notes file for the current version if it's not a prerelease.
    version = context.run("poetry version --short", hide=True)
    match = re.match(r"^(\d+)\.(\d+)\.\d+$", version.stdout.strip())
    if match:
        major = match.group(1)
        minor = match.group(2)
        release_notes_file = Path(__file__).parent / "docs" / "admin" / "release_notes" / f"version_{major}.{minor}.md"
        if not release_notes_file.exists():
            print(f"Release notes file `version_{major}.{minor}.md` does not exist.")
            raise Exit(code=1)


@task
def docs(context):
    """Build and serve docs locally for development."""
    exec_cmd = "mkdocs serve -v"
    run_command(context, exec_cmd, port="8001:8001")


@task(
    help={
        "version": "Version of schema_enforcer to generate the release notes for.",
        "date": "Date of the release (default: today).",
    }
)
def generate_release_notes(context, version="", date=""):
    """Generate Release Notes using Towncrier."""
    if not version:
        version = context.run("poetry version --short", hide=True).stdout.strip()

    version_major_minor = ".".join(version.split(".")[:2])
    context.run(f"poetry run python bin/ensure_release_notes.py --version {version_major_minor}")

    command = f"poetry run towncrier build --version {version} --yes"
    if date:
        command += f" --date {date}"
    # Due to issues with git repo ownership in the containers, this must always run locally.
    context.run(command)
>>>>>>> 31cc3ca (Cookie initially baked targeting develop by NetworkToCode Cookie Drift Manager Tool)
