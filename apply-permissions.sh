#!/bin/bash
./fix-permissions.sh
sudo parallel --colsep '☠️' chmod -f {1} '{4}' ';' chown -f -h {2}:{3} '{4}' :::: permissions.txt
