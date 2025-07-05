#!/bin/bash
if mountpoint -q /rpi/firmware; then
	echo "UNMOUNTING /rpi/firmware"
	sudo umount -f -l /rpi/firmware
fi

if mountpoint -q /rpi/root; then
	echo "UNMOUNTING /rpi/root"
	sudo umount -f -l /rpi/root
fi

if mountpoint -q /rpi/internals/base; then
	echo "UNMOUNTING /rpi/internals/base"
	sudo umount -f -l /rpi/internals/base
fi

sudo mount -o ro /rpi/internals/firmware.fat /rpi/firmware
sudo mount -o ro /rpi/internals/base.img /rpi/internals/base

sudo mount -t overlay overlay /rpi/root \
  -o lowerdir=/rpi/internals/base,upperdir=/rpi/internals/changes-base,workdir=/rpi/internals/workdir,\
index=on,nfs_export=on,redirect_dir=nofollow
