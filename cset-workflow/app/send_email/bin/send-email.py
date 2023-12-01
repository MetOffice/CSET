#! /usr/bin/env python3

"""Send a notification email linking to the output page.

Sends a notification email to the user of the workflow when it has completed,
with a link to the output webpage.
"""

import os
import subprocess


def get_home_page_addr():
    """Derive the address of the output page based directory structure."""
    path = os.getenv("WEB_DIR").split("/public_html/")
    if len(path) == 1:
        path = os.getenv("WEB_DIR").split("/Public/")
    if len(path) == 1:
        raise RuntimeError("Cannot determine web address.")
    return f"{os.getenv('WEB_ADDR').strip('/')}/{path[-1]}"


if __name__ == "__main__":
    subject = "CSET webpage ready"
    body = f"""The webpage for your run of CSET is now ready. You can view it here:\n{get_home_page_addr()}"""
    subprocess.run(
        f'printf "{body}" | mail -s "{subject}" -S "from=notifications" "$USER"',
        check=True,
        shell=True,
    )
