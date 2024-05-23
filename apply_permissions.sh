#!/bin/bash

# Read each line from the permissions file
while IFS=' ' read -r perm uid gid filepath; do
  # Adjust UID and GID
  new_uid=$((uid + 2000))
  new_gid=$((gid + 2000))

  # Change the ownership of the file
  chown -f -h $new_uid:$new_gid $filepath

  # Change the permissions of the file
  chmod -f $perm $filepath

done < permissions.txt
