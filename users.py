#!/bin/python
"""This script parses the etc/group and etc/passwd file and creates those
users and groups with a pid/gid offset and a prefix before the name"""

import pwd
import grp
import os


def user_exists(username):
    try:
        user_info = pwd.getpwnam(username)
        return user_info.pw_uid
    except KeyError:
        return False


def group_exists(groupname):
    try:
        group_info = grp.getgrnam(groupname)
        return group_info.gr_gid
    except KeyError:
        return False


def parse_passwd_file(passwd_file, offset, prefix):
    users_info = []
    try:
        with open(passwd_file, "r", encoding="UTF-8") as file:
            for line in file:
                if line.strip():  # Ensure the line is not empty
                    parts = line.split(":")
                    if (
                        len(parts) >= 4
                    ):  # Ensure there are enough parts to parse
                        username = parts[0]
                        uid = int(parts[2]) + offset
                        gid = int(parts[3]) + offset
                        users_info.append(
                            {
                                "username": prefix + username,
                                "uid": uid,
                                "gid": gid,
                            }
                        )
    except FileNotFoundError:
        print(f"The file {passwd_file} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return users_info


def parse_group_file(group_file, offset, prefix):
    group_info = []
    try:
        with open(group_file, "r", encoding="UTF-8") as file:
            for line in file:
                if line.strip():  # Ensure the line is not empty
                    parts = line.split(":")
                    if (
                        len(parts) >= 4
                    ):  # Ensure there are enough parts to parse
                        groupname = prefix + parts[0]
                        gid = int(parts[2]) + offset
                        members = parts[3].strip().split(",")
                        members = [prefix + member for member in members if member]
                        group_info.append(
                            {
                                "groupname": groupname,
                                "gid": gid,
                                "members": members,
                            }
                        )
    except FileNotFoundError:
        print(f"The file {group_file} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return group_info

def ask_promt(prompt):
    while True:
        response = input(f"{prompt} (yes/no) [yes]: ").strip().lower()
        if response == '' or response == 'yes' or response == 'y':
            return True
        elif response == 'no' or response == "n":
            return False
        else:
            print("Invalid response. Please enter 'yes' or 'no'.")
def create_user(username, uid, gid):
    result = os.system(f'sudo useradd -u {uid} -g {gid} {username}')
    if result != 0:
        raise RuntimeError(f"Failed to create user {username}:{uid}:{gid}")

def create_group(groupname, gid):
    result = os.system(f'sudo groupadd -g {gid} {groupname}')
    if result != 0:
        raise RuntimeError(f"Failed to create group {groupname}:{gid}")

def add_user_to_group(groupname, username):
    result = os.system(f'sudo usermod -aG {groupname} {username}')
    if result != 0:
        raise RuntimeError(f"Failed to create group {groupname}:{gid}")



users = parse_passwd_file("etc/passwd", 2000, "rpi-")
groups = parse_group_file("etc/group", 2000, "rpi-")

user_to_create = []
for user in users:
    local_uid = user_exists(user["username"])
    if local_uid:
        if local_uid != user["uid"]:
            raise Exception(f"User {user['username']}:{user['uid']} already exists with a different uid")
    else:
        user_to_create.append(user)
groups_to_create = []
for group in groups:
    local_gid = group_exists(group["groupname"])
    if local_gid:
        if local_gid != group["gid"]:
            raise Exception(f"Group {group['groupname']}:{group['gid']} already exists with a different gid")
    else:
        groups_to_create.append(group)

promt_result = ask_promt(f"Do you want to create the following users and groups?{users}{groups}")
if not promt_result:
    exit(0)

for group in groups_to_create:
    create_group(group["groupname"], group["gid"])
for user in user_to_create:
    create_user(user["username"], user["uid"], user["gid"])
for group in groups_to_create:
    for member in group["members"]:
        add_user_to_group(group["groupname"], member)

print("Users and groups created successfully.")
print("Plese consider to add your user to all the groups for git tracking reasons.")
prompt_result = ask_promt("Do you want to add your current user to the groups")
if not prompt_result:
    exit(0)

for group in groups:
    add_user_to_group(group["groupname"], os.getlogin())
