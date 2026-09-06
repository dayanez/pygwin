import sys
from pathlib import Path
from subprocess import check_output

import pytest

from pygwin.pytest.tools import ON_WINDOWS


@pytest.mark.parametrize("dir_name", ["venv", "venv with space"])
def test_pygwin_activator(tmp_path, dir_name):
    # Create virtualenv. ``--activators pygwin`` is required: virtualenv ships its
    # own built-in xonsh activator (unrelated to any xonsh install, baked into the
    # virtualenv package itself) that also targets "activate.xsh". Without pinning
    # the activator, whichever of the two runs last silently overwrites the other's
    # file, and the loser's activate.xsh ends up written for the wrong shell.
    venv_dir = tmp_path / dir_name
    assert b"PygwinActivator" in check_output(
        [sys.executable, "-m", "virtualenv", "--activators", "pygwin", str(venv_dir)]
    )
    assert venv_dir.is_dir()

    # Check activation script created
    if ON_WINDOWS:
        bin_path = venv_dir / "Scripts"
    else:
        bin_path = venv_dir / "bin"
    activate_path = bin_path / "activate.xsh"
    assert activate_path.is_file()

    # Sanity
    original_python = check_output(
        [
            sys.executable,
            "-m",
            "pygwin",
            "-c",
            "import shutil; shutil.which('python') or shutil.which('python3')",
        ]
    ).decode()
    assert Path(original_python).parent != bin_path

    # Activate
    venv_python = check_output(
        [
            sys.executable,
            "-m",
            "pygwin",
            "-c",
            f"source r'{activate_path}'; which python",
        ]
    ).decode()
    assert Path(venv_python).parent == bin_path

    # Deactivate
    deactivated_python = check_output(
        [
            sys.executable,
            "-m",
            "pygwin",
            "-c",
            f"source r'{activate_path}'; deactivate; "
            "import shutil; shutil.which('python') or shutil.which('python3')",
        ]
    ).decode()
    assert deactivated_python == original_python
