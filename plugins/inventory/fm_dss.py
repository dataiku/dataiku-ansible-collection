ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "dataiku-ansible-collection",
}

DOCUMENTATION = """
---
name: fm_dss
short_description: Generates inventory of DSS from FM
description: |
    This module queries a Fleet Manager and populates the inventory with the
    DSS found in it.

    ---
    plugin: dataiku.dss.fm_dss
    dataiku_fleet_managers:
    - id: <NAME>
      host: <HTTPS_HOST>
      instances:
        access_type: public_ip
        ssh:
          user: <DSS_SSH_USER>
        tags:
          - production
      api_key:
        file: "~/.config/dataiku/<NAME>.json"
        ssh_auto_create: true
      ssh:
        user: <FM_SSH_USER> # Ex: ec2-user
        host: <SSH_HOST> # Default to same than HTTPS if absent
        fm_user: <USER_NAME_IN_FM> # A FM user is required to have a key

author:
    - Jean-Bernard Jansen (jean-bernard.jansen@dataiku.com)
"""

from ansible.plugins.inventory import BaseInventoryPlugin
from ansible_collections.dataiku.dss.plugins.module_utils.utils import makeSimpleLogger
from requests import Session
from requests.auth import HTTPBasicAuth
import os
import subprocess
import json
import stat

logger = makeSimpleLogger(__name__)


class InventoryModule(BaseInventoryPlugin):
    NAME = "fm_dss"

    def __init__(self):
        super(InventoryModule, self).__init__()

    def parse(self, inventory, loader, path, cache=False):
        try:
            super(InventoryModule, self).parse(inventory, loader, path, cache)
            fleet_managers_config = loader.load_from_file(path)
            for fleet_manager in fleet_managers_config.get(
                "dataiku_fleet_managers", []
            ):
                fm_id = fleet_manager["id"]
                host = fleet_manager["host"]
                port = str(fleet_manager.get("port", "443"))
                protocol = fleet_manager.get("protocol", "https")
                tenant_id = fleet_manager.get("tenant_id", "main")

                # Find API key
                api_key_config = fleet_manager["api_key"]
                api_key_id = None
                api_key_secret = None
                if "file" in api_key_config:
                    file_path = os.path.expanduser(api_key_config["file"])
                    if not os.path.exists(file_path) and api_key_config.get(
                        "ssh_auto_create", False
                    ):
                        ssh_user = fleet_manager["ssh"]["user"]
                        ssh_host = fleet_manager["ssh"].get("host", host)
                        ssh_fm_unix_user = fleet_manager["ssh"].get(
                            "fm_unix_user", "dataiku"
                        )
                        ssh_fm_user = fleet_manager["ssh"].get("fm_user", "admin")
                        ssh_fm_datadir = fleet_manager["ssh"].get(
                            "datadir", "/data/dataiku/fmhome"
                        )
                        ssh_command = [
                            "ssh",
                            "-o",
                            "StrictHostKeyChecking=no",
                            "-o",
                            "BatchMode=yes",
                            "-o",
                            f"User={ssh_user}",
                            ssh_host,
                        ]
                        command = [
                            f"{ssh_fm_datadir}/bin/fmadmin",
                            "create-personal-api-key",
                            ssh_fm_user,
                        ]
                        if ssh_fm_unix_user != ssh_user:
                            command = ["sudo", "-u", ssh_fm_unix_user] + command
                        ssh_process = subprocess.Popen(
                            ssh_command + command,
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE,
                            close_fds=True,
                        )
                        stdout, stderr = ssh_process.communicate()
                        if ssh_process.returncode != 0:
                            raise Exception(
                                f"Failed to execute ssh command. stdout={stdout} stderr={stderr}"
                            )
                        id = None
                        secret = None
                        for line in reversed(stdout.decode().splitlines()):
                            if line.startswith("Key id: "):
                                id = line[8:]
                            if line.startswith("Key secret: "):
                                secret = line[12:]
                            if id is not None and secret is not None:
                                break
                        api_key_id = id
                        api_key_secret = secret
                        with open(file_path, "w") as file:
                            json.dump({"id": id, "secret": secret}, file, indent=2)
                        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
                    else:
                        with open(file_path, "r") as file:
                            api_key_data = json.load(file)
                            api_key_id = api_key_data["id"]
                            api_key_secret = api_key_data["secret"]
                elif "aws_secret_manager" in api_key_config:
                    logger.fatal("aws_secret_manager fetch method not implemented.")
                elif "azure_vault" in api_key_config:
                    logger.fatal("azure_vault fetch method not implemented.")
                elif "gcp_secret_manager" in api_key_config:
                    logger.fatal("gcp_secret_manager fetch method not implemented.")

                # Get list of instances
                session = Session()
                session.auth = HTTPBasicAuth(api_key_id, api_key_secret)
                instances_config = fleet_manager["instances"]
                network_access = instances_config.get("access_type", "public_ip")
                instance_ssh_user = instances_config["ssh"]["user"]
                required_fm_tags = instances_config.get("required_fm_tags",[])

                # Get vnets
                request = session.request(
                    "GET",
                    f"{protocol}://{host}:{port}/api/public/tenants/{tenant_id}/virtual-networks",
                )
                request.raise_for_status()
                vnets_list = request.json()
                vnets = {}
                vnets_inventory = {}
                inventory.add_group(f"fm-{fm_id}-{tenant_id}")
                tenant_group = inventory.groups[f"fm-{fm_id}-{tenant_id}"]
                for vnet in vnets_list:
                    vnets[vnet["id"]] = vnet
                    group_name = f"fm-{fm_id}-{tenant_id}-{vnet['label']}"
                    inventory.add_group(group_name)
                    vnet_group = inventory.groups[group_name]
                    tenant_group.add_child_group(vnet_group)
                    vnets_inventory[vnet["id"]] = vnet_group

                # Get instance templates
                # request = session.request("GET",f"{protocol}://{host}:{port}/api/public/tenants/{tenant_id}/instance-settings-templates")
                # request.raise_for_status()
                # templates_list = request.json()
                # templates = { t["id"]: t for t in templates_list }

                # Get instances
                request = session.request(
                    "GET",
                    f"{protocol}://{host}:{port}/api/public/tenants/{tenant_id}/instances",
                )
                request.raise_for_status()
                instances = request.json()

                for instance in instances:
                    logical_instance_id = instance["id"]
                    node_id = instance["label"]
                    vnet_id = instance["virtualNetworkId"]
                    vnet_name = instance["virtualNetworkLabel"]
                    settings_id = instance["instanceSettingsTemplateId"]
                    settings_name = instance["instanceSettingsTemplateLabel"]
                    inventory_hostname = f"fm-{fm_id}-{tenant_id}-{node_id}"

                    # Check tags
                    if not set(required_fm_tags).issubset(set(instance["fmTags"])):
                        logger.info(
                            f"Instance {inventory_hostname} skipped, not matching required tags."
                        )
                        continue


                    # Physical instance info
                    request = session.request(
                        "GET",
                        f"{protocol}://{host}:{port}/api/public/tenants/{tenant_id}/instances/{logical_instance_id}/status",
                    )
                    request.raise_for_status()
                    status = request.json()

                    if status.get("hasPhysicalInstance", False) and status.get("cloudMachineIsUp", False):
                        self.inventory.add_host(inventory_hostname)
                        inventory_host = self.inventory.hosts[inventory_hostname]
                        vnets_inventory[vnet_id].add_host(inventory_host)
                        if network_access == "public_dns":
                            ansible_host = status["publicDNS"]
                        elif network_access == "private_dns":
                            ansible_host = status["privateDNS"]
                        elif network_access == "private_ip":
                            ansible_host = status["privateIP"]
                        else:
                            ansible_host = status["publicIP"]
                        inventory_host.set_variable("ansible_host", ansible_host)
                        inventory_host.set_variable("ansible_user", instance_ssh_user)
                        dataiku_facts = {
                            "dss": {
                                "image_id": instance["imageId"],
                                "port": "10000",
                                "datadir": "/data/dataiku/dss_data",
                                "node_id": node_id,
                                "node_type": instance["dssNodeType"],
                                "logical_instance_id": logical_instance_id,
                            }
                        }
                        inventory_host.set_variable("dataiku", dataiku_facts)
                        logger.info(
                            f"Generated data for instance {inventory_hostname} in group {vnets_inventory[vnet_id].name}"
                        )
                    else:
                        logger.info(
                            f"Instance {inventory_hostname} is ignored because physical instance is not found."
                        )
        except Exception as e:
            logger.error(e, exc_info=True)
