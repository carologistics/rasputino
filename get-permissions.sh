#!/bin/bash
output_file="permissions.txt"
./fix-permissions.sh
# Find all files, directories, and symlinks and get their permissions, UID, and GIDj
g++ -std=c++20 -o /tmp/get-permissions get.cpp && /tmp/get-permissions > "$output_file"
echo "Permissions written to $output_file"
