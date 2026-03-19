#!/bin/sh
# Detect OS
. /etc/os-release

if [[ "$ID" == "ubuntu" || "$ID_LIKE" == *"debian"* ]]; then
    NFS_SERVICE="nfs-kernel-server"
else
    # Fedora / RHEL
    NFS_SERVICE="nfs-server"
fi

sudo systemctl stop "${NFS_SERVICE}.service"

if mountpoint -q /rpi/root; then
	echo "UNMOUNTING /rpi/root"
	sudo umount -f -l /rpi/root
fi

sudo rm -rf /rpi/internals/changes-base/*
sudo rm -rf /rpi/internals/workdir/*

sudo mount -t overlay overlay /rpi/root \
  -o lowerdir=/rpi/internals/base,upperdir=/rpi/internals/changes-base,workdir=/rpi/internals/workdir,\
index=on,nfs_export=on,redirect_dir=nofollow

sudo systemctl start "${NFS_SERVICE}.service"
