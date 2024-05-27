#!/bin/bash
output_file="permissions.txt"
./fix-permissions.sh
# Find all files, directories, and symlinks and get their permissions, UID, and GIDj
find . | sed -e 's/\\/\\\\/g' -e 's/ /\\ /g' | grep -vf .permignore | xargs -I '{}' stat --format "%a☠️%u☠️%g☠️%n" '{}' > $output_file
echo "Permissions written to $output_file"
