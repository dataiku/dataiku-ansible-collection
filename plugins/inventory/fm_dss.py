#!/usr/bin/python

ANSIBLE_METADATA = {"metadata_version": "1.1", "status": ["preview"], "supported_by": "dataiku-ansible-collection"}

DOCUMENTATION = """
---
plugin: fm_dss
short_description: Generates inventory of DSS from FM
description:
    This module queries a Fleet Manager and populates the inventory with the 
    DSS found in it.
"""

from ansible.plugins.inventory import BaseInventoryPlugin
from ansible_collections.dataiku.dss.plugins.module_utils.utils import makeSimpleLogger
from requests import Session
from requests import exceptions
from requests.auth import HTTPBasicAuth
import sys
import logging
import os
import subprocess
import json
import stat

logger = makeSimpleLogger(__name__)

class InventoryModule(BaseInventoryPlugin):
    NAME = 'fm_dss'

    def __init__(self):
        super(InventoryModule, self).__init__()

    def parse(self, inventory, loader, path, cache=False):
        try:
            super(InventoryModule, self).parse(inventory, loader, path, cache)
            fleet_managers_config = loader.load_from_file(path)
            for fleet_manager in fleet_managers_config.get("dataiku_fleet_managers", []):
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
                    if not os.path.exists(file_path) and "ssh_auto_create" in api_key_config:
                        ssh_user = fleet_manager["ssh"]["user"]
                        ssh_host = fleet_manager["ssh"].get("host", host)
                        ssh_fm_unix_user = fleet_manager["ssh"].get("fm_unix_user", "dataiku")
                        ssh_fm_user = fleet_manager["ssh"].get("fm_user", "admin")
                        ssh_fm_datadir = fleet_manager["ssh"].get("datadir", "/data/dataiku/fmhome")
                        ssh_command = [
                                "ssh",
                                "-o", "StrictHostKeyChecking=no",
                                "-o", "BatchMode=yes",
                                "-o", f"User={ssh_user}",
                                ssh_host,
                                ]
                        command = [f"{ssh_fm_datadir}/bin/fmadmin","create-personal-api-key", ssh_fm_user]
                        if ssh_fm_unix_user != ssh_user:
                            command = ["sudo", "-u", ssh_fm_unix_user] + command
                        ssh_process = subprocess.Popen(ssh_command+command,shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, close_fds=True)
                        stdout, stderr = ssh_process.communicate()
                        if ssh_process.returncode != 0:
                            raise Exception(f"Failed to execute ssh command. stdout={stdout} stderr={stderr}")
                        id = None
                        secret = None
                        for line in reversed(stdout.decode().splitlines()):
                            if line.startswith("Key id: "):
                                id = line[8:]
                            if line.startswith("Key secret: "):
                                secret = line[12:]
                            if id != None and secret != None:
                                break
                        api_key_id = id
                        api_key_secret = secret
                        with open(file_path,"w") as file:
                            json.dump({"id": id, "secret": secret}, file, indent=2)
                        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
                    else:
                        with open(file_path,"r") as file:
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

                # Get vnets
                request = session.request("GET",f"{protocol}://{host}:{port}/api/public/tenants/{tenant_id}/virtual-networks")
                request.raise_for_status()
                vnets_list = request.json()
                vnets = {}
                vnets_inventory = {}
                tenant_group = inventory.add_group(f"fm-{fm_id}-{tenant_id}")
                for vnet in vnets_list:
                    vnets[vnet["id"]] = vnet
                    vnets_inventory[vnet["id"]] = tenant_group.add_child_group(f"fm-{fm_id}-{tenant_id}-{vnet.label}")

                # Get instance templates
                # request = session.request("GET",f"{protocol}://{host}:{port}/api/public/tenants/{tenant_id}/instance-settings-templates")
                # request.raise_for_status()
                # templates_list = request.json()
                # templates = { t["id"]: t for t in templates_list }

                # Get instances
                request = session.request("GET",f"{protocol}://{host}:{port}/api/public/tenants/{tenant_id}/instances")
                request.raise_for_status()
                instances = request.json()

                for instance in instances:
                    logical_instance_id = instance["id"]
                    node_id = instance["label"]
                    inventory_hostname = f"fm-{fm_id}-{tenant_id}-{node_id}"

                    # Physical instance info
                    request = session.request("GET",f"{protocol}://{host}:{port}/api/public/tenants/{tenant_id}/instances/{logical_instance_id}/status)")
                    request.raise_for_status()
                    status = request.json()
                    
                    

                logger.info(json.dumps(vnets,indent=2))
                logger.info(json.dumps(templates,indent=2))
                logger.info(json.dumps(instances,indent=2))



        except Exception as e:
            logger.error(e, exc_info=True)

        self.inventory.add_host("robert")
        self.inventory.set_variable("robert", "ansible_host", "robert.com")
        #print(json.dumps(inventory,indent=2))
