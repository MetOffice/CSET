# © Crown copyright, Met Office (2022-2024) and CSET contributors.
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

"""Tests for send_email workflow utility."""

import subprocess

import pytest

from CSET._workflow_utils import send_email


def test_get_home_page_address_public_html(monkeypatch):
    """Test public_html path gets parsed properly."""
    monkeypatch.setenv("WEB_DIR", "/home/user/public_html/CSET")
    monkeypatch.setenv("WEB_ADDR", "https://example.com/~user")
    expected = "https://example.com/~user/CSET"
    actual = send_email.get_home_page_address()
    assert actual == expected


def test_get_home_page_address_Public(monkeypatch):
    """Test Public path and trailing slash on WEB_ADDR."""
    monkeypatch.setenv("WEB_DIR", "/home/user/Public/CSET")
    monkeypatch.setenv("WEB_ADDR", "https://example.com/~user/")
    expected = "https://example.com/~user/CSET"
    actual = send_email.get_home_page_address()
    assert actual == expected


def test_get_home_page_address_no_known_web_directory(monkeypatch):
    """Exception when web directory cannot be determined."""
    monkeypatch.setenv("WEB_DIR", "/home/user/CSET")
    monkeypatch.setenv("WEB_ADDR", "https://example.com/~user")
    with pytest.raises(ValueError, match="Cannot determine web address."):
        send_email.get_home_page_address()


def test_get_home_page_address_no_WEB_DIR(monkeypatch):
    """Exception when WEB_DIR not set."""
    monkeypatch.setenv("WEB_ADDR", "https://example.com/~user")
    with pytest.raises(ValueError, match="WEB_DIR not set."):
        send_email.get_home_page_address()


def test_get_home_page_address_no_WEB_ADDR(monkeypatch):
    """Exception when WEB_ADDR not set."""
    monkeypatch.setenv("WEB_DIR", "/home/user/Public/CSET")
    with pytest.raises(ValueError, match="WEB_ADDR not set."):
        send_email.get_home_page_address()


def test_send_email(monkeypatch):
    """Test send_email run."""
    monkeypatch.setenv("WEB_DIR", "/home/user/public_html/CSET")
    monkeypatch.setenv("WEB_ADDR", "https://example.com/~user")

    def mock_subprocess_run(args, check, shell):
        assert (
            args
            == 'printf "The webpage for your run of CSET is now ready. You can view it here:\nhttps://example.com/~user/CSET" | mail -s "CSET webpage ready" -S "from=notifications" "$USER"'
        )
        assert check
        assert shell

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    send_email.run()


def test_send_email_invalid_environment_variables(monkeypatch):
    """Test send_email run."""

    def mock_subprocess_run(args, check, shell):
        assert (
            args
            == 'printf "The webpage for your run of CSET is now ready, though the address could not be determined.\nCheck that WEB_ADDR and WEB_DIR are set correctly, then consider filing a bug report at https://github.com/MetOffice/CSET" | mail -s "CSET webpage ready" -S "from=notifications" "$USER"'
        )
        assert check
        assert shell

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    send_email.run()
