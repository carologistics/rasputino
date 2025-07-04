#!/bin/sh

sudo systemctl stop nfs-server.service

if mountpoint -q /rpi/root; then
	echo "UNMOUNTING /rpi/root"
	sudo umount -f -l /rpi/root
fi

sudo rm -rf /rpi/internals/changes-base/*
sudo rm -rf /rpi/internals/workdir/*

sudo mount -t overlay overlay /rpi/root \
  -o lowerdir=/rpi/internals/base,upperdir=/rpi/internals/changes-base,workdir=/rpi/internals/workdir,\
index=on,nfs_export=on,redirect_dir=nofollow

sudo systemctl start nfs-server.service
