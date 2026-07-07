#!/usr/bin/env bash
# Check conda lockfiles are up-to-date.
set -eu

if ! sha256sum -c requirements/locks/sources
then
  echo "Conda lockfiles are outdated. Please run 'make update-dev-deps' to update them."
  exit 1
fi
