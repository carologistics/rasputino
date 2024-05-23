#!/bin/bash
output_file="permissions.txt"

# Find all files, directories, and symlinks and get their permissions, UID, and GIDj
find . | sed 's/\\/\\\\/g' | grep -vf .permignore | xargs -I '{}' stat --format '%a %u %g %n' '{}' | awk '{gsub(/^rpi-/, "", $2); gsub(/^rpi-/, "", $3); printf "%s %s %s", $1, $2, $3; for (i=4; i<=NF; i++) printf " %s", $i; print ""}' > $output_file
#done > $output_file
echo "Permissions written to $output_file"
#while IFS= read -d '' -r file; do
