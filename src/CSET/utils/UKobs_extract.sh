#!/usr/bin/bash

# Usage: ./UKobs_extract.sh <path_to_tar_file> <path_to_save_output>

###### UK ######

# Check if tar file is empty or invalid
if ! tar -tf "$1" >/dev/null 2>&1 || [ -z "$(tar -tf "$1")" ]; then
    echo "Error: Tar file is empty or invalid: $1"
    exit 1
fi

# Create temporary directory for untarred files
uk_temp_dir="$2/uk_obstore"
mkdir -p "$uk_temp_dir"

# Extract tar files to temporary directory
tar -xf "$1" -C "$uk_temp_dir"
gunzip "$uk_temp_dir"/*.gz
