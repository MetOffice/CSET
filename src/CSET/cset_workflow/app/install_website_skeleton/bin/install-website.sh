#!/usr/bin/env bash

# Copies the static files for the web interface into the correct location, and
# creates a symbolic link under the web server's document root.

set -euo pipefail
IFS="$(printf '\n\t')"

# Strip trailing slashes in case they have been added in the config. Otherwise
# they break the symlinks.
WEB_DIR="${WEB_DIR%/}"

# Remove existing output ahead of creating new symlink.
echo "Removing any existing output link at $WEB_DIR"
rm -vfr -- "$WEB_DIR"

echo "Installing website files to $WEB_DIR"
# If we end up needing a build step for the website, here is where to run it.

# Create directory for web content.
mkdir -v "${CYLC_WORKFLOW_SHARE_DIR}/web"
# Copy static HTML/CSS/JS.
cp -rv html/* "${CYLC_WORKFLOW_SHARE_DIR}/web"
# Create directory for plots.
mkdir -p "${CYLC_WORKFLOW_SHARE_DIR}/web/plots"

# Ensure parent directories of WEB_DIR exist.
mkdir -p "$(dirname "$WEB_DIR")"

# Create symbolic link to web directory.
# NOTE: While good for space, it means `cylc clean` removes output.
ln -s "${CYLC_WORKFLOW_SHARE_DIR}/web" "$WEB_DIR"
