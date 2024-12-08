#! /usr/bin/env python3

"""Send a notification email linking to the output page.

Sends a notification email to the user of the workflow when it has completed,
with a link to the output webpage.
"""

import os
import subprocess


def get_home_page_address():
    """Derive the address of the output page based directory structure."""
    try:
        web_dir = os.environ["WEB_DIR"]
    except KeyError as err:
        raise ValueError("WEB_DIR not set.") from err
    try:
        web_addr = os.environ["WEB_ADDR"]
    except KeyError as err:
        raise ValueError("WEB_ADDR not set.") from err

    path = web_dir.split("/public_html/")
    if len(path) == 1:
        path = os.getenv("WEB_DIR").split("/Public/")
    if len(path) == 1:
        raise ValueError("Cannot determine web address.")
    base_address = web_addr.strip("/")
    return f"{base_address}/{path[-1]}"


def run():
    """Run workflow script."""
    subject = "CSET webpage ready"
    try:
        body = f"The webpage for your run of CSET is now ready. You can view it here:\n{get_home_page_address()}"
    except ValueError:
        body = "The webpage for your run of CSET is now ready, though the address could not be determined.\nCheck that WEB_ADDR and WEB_DIR are set correctly, then consider filing a bug report at https://github.com/MetOffice/CSET"
    subprocess.run(
        f'printf "{body}" | mail -s "{subject}" -S "from=notifications" "$USER"',
        check=True,
        shell=True,
    )
