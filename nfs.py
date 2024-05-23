#!/bin/python
"""Generates the local and server idmap config"""

from jinja2 import Environment, FileSystemLoader


def parse_passwd_file(passwd_file):
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
                        users_info.append({f"{username}": username})
    except FileNotFoundError:
        print(f"The file {passwd_file} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return users_info


def parse_group_file(group_file):
    group_info = []
    try:
        with open(group_file, "r", encoding="UTF-8") as file:
            for line in file:
                if line.strip():  # Ensure the line is not empty
                    parts = line.split(":")
                    if len(parts) >= 4:
                        groupname = parts[0]
                        group_info.append({f"{groupname}": groupname})
    except FileNotFoundError:
        print(f"The file {group_file} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return group_info


users = parse_passwd_file("etc/passwd")
groups = parse_group_file("etc/group")
user_mappings = {k: v for d in users for k, v in d.items()}
group_mappings = {k: v for d in groups for k, v in d.items()}
config_data = {
    "domain": "raspberry",
    "user_mappings": user_mappings,
    "group_mappings": group_mappings,
}
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('idmapd.conf.j2')
idmapd_conf_content = template.render(config_data)
with open('etc/idmapd.conf', 'w') as f:
    f.write(idmapd_conf_content)
print("client idmapd.conf file has been generated and written to etc/idmapd.conf")

user_server = {k: "rpi-" + v for k, v in user_mappings.items()}
group_server = {k: "rpi-" + v for k, v in group_mappings.items()}

config_server = {
    "domain": "raspberry",
    "user_mappings": user_server,
    "group_mappings": group_server,
}
idmapd_conf_server = template.render(config_server)
with open('/etc/idmapd.conf', 'w') as f:
    f.write(idmapd_conf_server)
print("server idmapd.conf file has been generated and written to /etc/idmapd.conf")
