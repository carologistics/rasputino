#!/bin/bash

# Read each line from the permissions file
while IFS=' ' read -r perm user group filepath; do
  # Adjust UID and GID

  # Change the ownership of the file
  chown -h $user:$group "$filepath"

  # Change the permissions of the file
  chmod -f $perm $filepath

done < <(awk '{printf "%s %s %s ", $1, $2, $3; for(i=4; i<=NF; i++) printf "%s ", $i; print ""}' permissions.txt)
