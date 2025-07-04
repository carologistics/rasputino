#!/bin/bash

sudo systemctl stop dhcpd.service
sudo systemctl stop nfs-server.service
sudo systemctl stop tftp.socket
sudo systemctl stop tftp.service

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

sudo rm -rf /rpi

sudo mkdir -p /rpi/internals
sudo mkdir -p /rpi/firmware
sudo mkdir -p /rpi/root
sudo mkdir -p /rpi/internals/workdir
sudo mkdir -p /rpi/internals/changes-base
sudo mkdir -p /rpi/internals/base

sudo wget -O /rpi/pi.img.xz https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2025-05-13/2025-05-13-raspios-bookworm-arm64-lite.img.xz

sudo unxz /rpi/pi.img.xz
#
# TODO TOOGLE
# cp pi.img /rpi/pi.img
IMG=/rpi/pi.img

ETH_IF=$(nmcli -t -f DEVICE,TYPE device status | grep ':ethernet$' | cut -d: -f1)
echo $ETH_IF
IP=$(ifconfig $ETH_IF | awk '/inet / && $2 !~ /^127/ {print $2; exit}')
echo $IP

echo "server $IP iburst" > chrony.sources

  # --batch \
export SDM_LOG_LEVEL=debug

sudo ../sdm \
  --extend --xmb 2048 \
  $IMG

# TODO libcamera-apps
sudo ../sdm \
  --customize \
  --plugin user:"adduser=robotino|password=dynabot|uid=1000" \
  --plugin disables:piwiz \
  --plugin L10n:host \
  --plugin copyfile:"from=camera-server.service|to=/etc/systemd/system/" \
  --plugin system:"service-enable=camera-server.service" \
  --plugin apps:"apps=vim libcamera-dev python3-libcamera libcap-dev python3-dev build-essential libgl1-mesa-glx python3-kms++" \
  --plugin venv:"path=/home/robotino/venv|create=true|requirements=object-detection/requirements.txt|createoptions=--system-site-packages" \
  --cscript ./config-phase \
  --custom1 $IP \
  --plugin chrony:"sources=chrony.sources|nodistsources" \
  --apt-options noupgrade \
  --regen-ssh-host-keys \
  $IMG


rm chrony.sources

sudo 7z x $IMG -o/rpi/internals

sudo rm $IMG

sudo mv /rpi/internals/0.fat /rpi/internals/firmware.fat
sudo mv /rpi/internals/1.img /rpi/internals/base.img

sudo mount -o ro /rpi/internals/firmware.fat /rpi/firmware
sudo mount -o ro /rpi/internals/base.img /rpi/internals/base

sudo mount -t overlay overlay /rpi/root \
  -o lowerdir=/rpi/internals/base,upperdir=/rpi/internals/changes-base,workdir=/rpi/internals/workdir,\
index=on,nfs_export=on,redirect_dir=nofollow

sudo systemctl restart dhcpd.service
sudo systemctl restart nfs-server.service
sudo systemctl restart tftp.service
