#!/usr/bin/bash

# Check if directory contains any files
if [ -z "$(find "$1" -type f)" ]; then
    echo "Error: Input directory is empty (no files found): $1"
    exit 1
fi

# Check if all files are empty
if [ -z "$(find "$1" -type f -size +0)" ]; then
    echo "Error: All files in input directory are empty: $1"
    exit 1
fi

# Create temporary directory for untarred files
temp_dir="$2/obstore"
mkdir -p "$temp_dir"

# Extract tar files to temporary directory
if [[ "$1" == *.tar || "$1" == *.tar.* ]]; then
    tar -xf "$1" -C "$temp_dir"
else
    # Not a tar file, ignore
    echo "no .tar files in $1, ignoring.."
fi

# Gunzip files only if .gz files exist
if compgen -G "$temp_dir"/*.gz > /dev/null; then
    gunzip "$temp_dir"/*.gz
else
    echo "no .gz files in $temp_dir, ignoring.."
fi

echo "Script finished, output at $temp_dir"
