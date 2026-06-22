"""
Helper script to install the Alpha Crowds addon into Blender.

Usage:
    python install.py --blender /path/to/blender

Or set BLENDER_PATH environment variable and run:
    python install.py
"""

import argparse
import os
import shutil
import subprocess
import sys


def get_blender_addons_path(blender_exe: str) -> str:
    script = (
        "import bpy, os; "
        "print(bpy.utils.user_resource('SCRIPTS', path='addons'))"
    )
    result = subprocess.run(
        [blender_exe, "--background", "--python-expr", script],
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if os.sep in line or "/" in line:
            return line.strip()
    raise RuntimeError("Could not determine Blender addons path")


def install(blender_exe: str) -> None:
    addon_src = os.path.dirname(os.path.abspath(__file__))
    addons_dir = get_blender_addons_path(blender_exe)
    dest = os.path.join(addons_dir, "alpha_crowds")

    if os.path.exists(dest):
        shutil.rmtree(dest)

    shutil.copytree(addon_src, dest, ignore=shutil.ignore_patterns("*.pyc", "__pycache__", ".git*", "install.py"))
    print(f"Installed Alpha Crowds to: {dest}")
    print("Restart Blender and enable the addon under Edit > Preferences > Add-ons")


def main():
    parser = argparse.ArgumentParser(description="Install Alpha Crowds Blender addon")
    parser.add_argument("--blender", default=os.environ.get("BLENDER_PATH", "blender"),
                        help="Path to Blender executable")
    args = parser.parse_args()
    install(args.blender)


if __name__ == "__main__":
    main()
