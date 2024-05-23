#!/bin/bash
output_file="permissions.txt"

# Find all files, directories, and symlinks and get their permissions, UID, and GID
find . -exec stat --format '%a %u %g %n' {} \; > "$output_file"

echo "Permissions written to $output_file"
