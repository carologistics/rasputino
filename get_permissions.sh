#!/bin/bash
output_file="permissions.txt"
username=$(whoami)
sudo setfacl -d -m "u:$username:rwx" -R .
sudo setfacl -m "u:$username:rwx" -R .
# Find all files, directories, and symlinks and get their permissions, UID, and GIDj
find . | sed -e 's/\\/\\\\/g' -e 's/ /\\ /g' | grep -vf .permignore | xargs -I '{}' stat --format "%a☠️%u☠️%g☠️%n" '{}' > $output_file
sudo chown -R "$UID:$GID" .git
#done > $output_file
echo "Permissions written to $output_file"
#while IFS= read -d '' -r file; do
