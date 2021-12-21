"""Tasks for use with Invoke."""
import os
import sys
from distutils.util import strtobool
from invoke import task

try:
    import toml
except ImportError:
    sys.exit("Please make sure to `pip install toml` or enable the Poetry shell and run `poetry install`.")


def project_ver():
    """Find version from pyproject.toml to use for docker image tagging."""
    with open("pyproject.toml", encoding="utf-8") as config_file:
        return toml.load(config_file)["tool"]["poetry"].get("version", "latest")


def is_truthy(arg):
    """Convert "truthy" strings into Booleans.

    Examples:
        >>> is_truthy('yes')
        True

    Args:
        arg (str): Truthy string (True values are y, yes, t, true, on and 1; false values are n, no,
        f, false, off and 0. Raises ValueError if val is anything else.
    """
    if isinstance(arg, bool):
        return arg
    return bool(strtobool(arg))


PYPROJECT_CONFIG = toml.load("pyproject.toml")
TOOL_CONFIG = PYPROJECT_CONFIG["tool"]["poetry"]

# Can be set to a separate Python version to be used for launching or building image
PYTHON_VER = os.getenv("PYTHON_VER", "3.7")
# Can be set to a separate ANsible version to be used for launching or building image
ANSIBLE_VER = os.getenv("ANSIBLE_VER", "2.10.8")
ANSIBLE_PACKAGE = os.getenv("ANSIBLE_PACKAGE", "ansible-base")
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
    if with_ansible:
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

    Returns:
        result (obj): Contains Invoke result from running task.
    """
    name = _get_image_name(with_ansible)

    if INVOKE_LOCAL:
        print(f"LOCAL - Running command {exec_cmd}")
        result = context.run(exec_cmd, pty=True)
    else:
        print(f"DOCKER - Running command: {exec_cmd} container: {name}")
        result = context.run(f"docker run -it -v {PWD}:/local {name} sh -c '{exec_cmd}'", pty=True)

    return result


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


@task(
    help={
        "cache": "Whether to use Docker's cache when building images (default enabled)",
        "force_rm": "Always remove intermediate images",
        "hide": "Suppress output from Docker",
    }
)
def build(context, cache=True, force_rm=False, hide=False):
    """This will build an image with the provided name and python version.

    Args:
        context (obj): Used to run specific commands
        cache (bool): Do not use cache when building the image
        force_rm (bool): Always remove intermediate containers
        hide (bool): Suppress output from docker build
    """
    build_image(context, cache, force_rm, hide=hide)
    build_image(context, cache, force_rm, hide=hide, with_ansible=True)


@task
def clean(context):
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


@task
def pylint(context):
    """This will run pylint for the specified name and Python version.

    Args:
        context (obj): Used to run specific commands
    """
    exec_cmd = 'find . -name "*.py" | xargs pylint'
    run_cmd(context, exec_cmd, with_ansible=True)


@task
def yamllint(context):
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

    Args:
        context (obj): Used to run specific commands
    """
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
    print("All tests have passed!")


@task
def cli(context, with_ansible=False):
    """This will enter the image to perform troubleshooting or dev work.

    Args:
        context (obj): Used to run specific commands
        with_ansible (str): Attach to container with ansible version specified by the 'ANSIBLE_VER' env var
    """
    name = _get_image_name(with_ansible)
    dev = f"docker run -it -v {PWD}:/local {name} /bin/bash"
    context.run(f"{dev}", pty=True)
