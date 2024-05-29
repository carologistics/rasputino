#!/bin/bash
#./fix-permissions.sh
g++ -o /tmp/apply-permissions apply.cpp -lacl && (sudo /tmp/apply-permissions) < permissions.txt
