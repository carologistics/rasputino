#!/bin/bash

sudo chown -R $(id -u):$(id -g) .git
username=$(whoami)
sudo setfacl -d -m "u:$username:rwx" -R .
sudo setfacl -m "u:$username:rwx" -R .

sudo parallel --colsep '☠️' chmod -f {1} '{4}' ';' chown -f -h {2}:{3} '{4}' :::: permissions.txt
