#!/bin/bash
username=$(whoami)
sudo setfacl -d -m "u:$username:rwx" -R .
sudo setfacl -m "u:$username:rwx" -R .
sudo chown -R $(id -u):$(id -g) .git
