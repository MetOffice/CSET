#!/bin/bash

# Copies the static files for the web interface into the correct location,
# optionally removing previous files there.

set -euo pipefail
IFS="$(printf '\n\t')"

if [[ "$CLEAN_WEB_DIR" == True ]]; then
  echo "Removing existing files at $WEB_DIR"
  rm -rf -- "$WEB_DIR"
fi

echo "Installing website files to $WEB_DIR"
# If we end up needing a build step for the website, here is where to run it.

# Copy static HTML/CSS/JS.
if mkdir -v "$WEB_DIR"; then
  cp -rv html/* "$WEB_DIR"
else
  # Fail task if directory already exists.
  >&2 echo "Web directory already exists, refusing to overwrite."
  >&2 echo "Web directory: $WEB_DIR"
  false
fi
