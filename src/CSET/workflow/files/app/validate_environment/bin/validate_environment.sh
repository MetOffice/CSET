#!/usr/bin/env bash

# Check the environment works and that CSET is installed.

set -euo pipefail

# Basic test that CSET is installed correctly.
echo "CSET location:"
command -v cset

echo "CSET version:"
cset --version

echo "Runtime environment:"
env
