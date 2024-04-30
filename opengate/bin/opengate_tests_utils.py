#!/usr/bin/env python3

import site
import os
import click


def return_site_packages_dir():
    site_package = [p for p in site.getsitepackages() if "site-packages" in p][0]
    return site_package


def get_site_packages_dir():
    print(return_site_packages_dir())


def get_libG4processes_path():
    for element in os.listdir(
        os.path.join(return_site_packages_dir(), "opengate_core.libs")
    ):
        if "libG4processes" in element:
            print(
                os.path.join(return_site_packages_dir(), "opengate_core.libs", element)
            )


def get_libG4geometry_path():
    for element in os.listdir(
        os.path.join(return_site_packages_dir(), "opengate_core.libs")
    ):
        if "libG4geometry" in element:
            print(
                os.path.join(return_site_packages_dir(), "opengate_core.libs", element)
            )


# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option("--path", "-p", default="", help="Path", required=True)
def go(path):
    """
    Tool to have the path of folders
    """
    if path == "libG4processes":
        get_libG4processes_path()
    elif path == "libG4geometry":
        get_libG4geometry_path()
    elif path == "site_packages":
        get_site_packages_dir()


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    go()
