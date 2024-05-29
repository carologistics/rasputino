#!/bin/bash
sudo chown -R $(id -u):$(id -g) .git
g++ -o /tmp/fix-permissions fix.cpp -lacl && sudo /tmp/fix-permissions
