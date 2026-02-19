# © Crown copyright, Met Office (2022-2026) and CSET contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Playwright browser tests for the CSET web interface."""

import http.server
import shutil
import tempfile
import threading
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def webserver():
    """Run a simple webserver serving static files. Its URL is returned."""
    # Prepare the static files in a temporary directory.
    tmp_path = Path(tempfile.mkdtemp())
    shutil.copytree(
        "src/CSET/cset_workflow/app/finish_website/file/html",
        tmp_path,
        dirs_exist_ok=True,
    )
    plot_dir = tmp_path / "plots-CACHEBUSTER"
    plot_dir.mkdir(exist_ok=True)
    shutil.copy("tests/test_data/index.jsonl", plot_dir)

    class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        """Serve files from the temporary directory."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs, directory=tmp_path)

    # Try ports until we find one, up to 100 tries.
    port = 8000
    webserver = None
    while not webserver and port < 8100:
        try:
            address = ("localhost", port)
            webserver = http.server.ThreadingHTTPServer(address, HTTPRequestHandler)
            break
        except OSError:
            port += 1
    if not webserver:
        raise OSError("No available ports in range 8000-8099.")

    # Start server in a separate thread.
    thread = threading.Thread(target=webserver.serve_forever, daemon=True)
    thread.start()

    # Return the localhost URL to the webserver.
    yield f"http://localhost:{port}/"

    # Shutdown the webserver once we return here.
    webserver.shutdown()


@pytest.mark.slow
def test_filter_title(page: Page, webserver: str):
    """Check that you can filter on title with the search box."""
    page.goto(webserver)

    # Check we can find the search box.
    expect(page.get_by_role("searchbox")).to_be_visible()

    # Filter diagnostics.
    page.get_by_role("searchbox").click()
    page.get_by_role("searchbox").fill('"Model A"')

    # Test the diagnostics correctly filtered. Check for Model B first so we
    # know it has finished doing the search.
    expect(page.get_by_role("heading", name="Model B").first).not_to_be_visible()
    expect(page.get_by_role("heading", name="Model A").first).to_be_visible()

    # Test clearing the filter.
    page.get_by_role("button", name="⌫ Clear search").click()
    expect(page.get_by_role("heading", name="Model A").first).to_be_visible()
    expect(page.get_by_role("heading", name="Model B").first).to_be_visible()


@pytest.mark.slow
def test_facet_dropdown(page: Page, webserver: str):
    """Test filtering diagnostics via the facet dropdowns."""
    page.goto(webserver)

    # Open the facets panel, then select a value for a facet.
    page.get_by_text("Search facet dropdowns").click()
    page.get_by_label("unique").select_option("foo")

    # Check we filtered correctly.
    expect(page.get_by_role("listitem")).to_contain_text("uniquefoo")
    # Line duplicated so we don't immediately close the browser during the demo.
    expect(page.get_by_role("listitem")).to_contain_text("uniquefoo")
