# -*- coding: utf-8 -*-
from typing import Dict, Any

from .yandex_cloud.yandex_api import *
from .linux_remote_control.ssh_console import *
from .linux_audit_parsers import *
import os
import pathlib


class YandexCloudParser:
    """
    Class encapsulating yandexAPI and methods for data retrieving
    """
    def __init__(self, oauth: str):
        """
        :param oauth: Ouath token for api
        """
        self.api = YandexAPI(oauth)
        self.server_placeholder = {
            "name": "", "id": "", "tag": "", "OS_name": "",
            "vulns": [], "ips": [], "services": [], "packages": []
        }

    def get_folder_id(self, org_name, cloud_name, folder_name) -> str:
        """
        Searches for specified folder in account cloud in specified organization
        :param org_name: Organization name
        :param cloud_name: Cloud name
        :param folder_name: Folder name
        :return: ID(str) of folder with specified name
        """
        orgs = self.api.get_all_organizations_list()
        org_id = ''
        for i in orgs:
            if i['name'] == org_name:
                org_id = i['id']
                break

        if org_id == '':
            raise Exception(f'No organization with name {org_name}')

        clouds = self.api.get_clouds_by_org_id(org_id)
        cloud_id = ''
        for i in clouds:
            if i['name'] == cloud_name:
                cloud_id = i['id']
                break

        if cloud_id == '':
            raise Exception(f'No cloud with name {cloud_name}')

        folders = self.api.get_folders_by_cloud_id(cloud_id)
        folder_id = ''
        for i in folders:
            if i['name'] == folder_name:
                folder_id = i['id']
                break

        if folder_id == '':
            raise Exception(f'No folder with name {folder_name}')
        return folder_id

    def get_cloud_objects(self, folder_id: str) -> dict[str, list[dict[str, dict]] | dict[str, dict]]:
        """
        Retrieving cloud objects(VMs, loadbalancers, object buckets, dns zones, databases and kubernets clusters) data
        via API calls.
        :param folder_id: ID of objects folder
        :return: Dictionary with cloud objects API data
        """

        virtual_machines = self.api.get_virtual_machines_list_by_folder_id(folder_id)
        kub_clusters = self.api.get_kubernets_clusters_by_folder_id(folder_id)
        dns_zones = self.api.get_dns_zones_by_folder_id(folder_id)
        lbs = self.api.get_loadbalancer_data_by_folder_id(folder_id)
        buckets = self.api.get_storage_buckets_by_folder_id(folder_id)

        db_list = ['postgresql', 'redis', 'mongodb',
                   'clickhouse', 'elasticsearch', 'greenplum',
                   'kafka', 'mysql', 'opensearch', 'sqlserver']

        dbs = {}
        for i in db_list:
            dbs[i] = {}
            clusters = self.api.get_db_clusters_by_folder_id(folder_id, i)
            for cluster in clusters:
                dbs[i][cluster] = self.api.get_dbs_by_cluster_id(cluster['id'], i)

        result = {
            'vms': virtual_machines,
            'k8s_clusters': kub_clusters,
            'dns_zones': dns_zones,
            'loadbalancers': lbs,
            'storage_buckets': buckets,
            'databases': dbs
        }

        return result

    def get_virtual_machines_ips(self, folder_id) -> dict:
        """
        Retrieving IPs and names of Virtual Machines in specified folder
        :param folder_id: ID of virtual machines folder
        :return: Dictionary ( {'id': {'name': 'value'} } )
        """
        # Get virtual machines list
        v_machines = self.api.get_virtual_machines_list_by_folder_id(folder_id)
        if len(v_machines) == 0:
            print(f'No virtual machines in folder with id {folder_id}')
            return dict()

        # Get virtual machines ips and names
        vm_data = dict()
        for machine in v_machines:
            data = self.api.get_virtual_machine_data_by_id(machine['id'])

            vm_data[machine['id']] = dict()
            vm_data[machine['id']]['name'] = data['name']

            for network_interface in data['networkInterfaces']:
                if 'address' in network_interface['primaryV4Address']['oneToOneNat'].keys():
                    vm_data[machine['id']]['ip'] = network_interface['primaryV4Address']['oneToOneNat']['address']
                else:
                    vm_data[machine['id']]['ip'] = ''

                    print(f"Machine's '{data['name']}' (id '{machine['id']}')"
                          f" has no public ip to connect.\n\tVM status: '{data['status']}'\n\t"
                          f"Net interface subnet id: '{network_interface['subnetId']}'")

        return vm_data

    def get_yacloud_server_objects(self, vms_data: dict, secrets: list[dict]) -> dict:
        """
        Retrieving audit data(services, packages, vulnerabilities, net Interfaces) for virtual machines.
        :param vms_data: Dictionary of virtual machines ( {'id': {'name': 'value'} } )
        :param secrets: List of credentials for ssh connection
        :return: Dictionary with servers objects ( {'servers': [] } )
        """
        servers = {'servers': []}

        for vm_id in vms_data.keys():
            server = self.server_placeholder.copy()
            server['id'] = vm_id
            server['name'] = vms_data[vm_id]['name']
            server['tag'] = ''
            flag = False
            if vms_data[vm_id]['ip'] == '':
                servers['servers'].append(server)
                continue
            for secret in secrets:
                if vm_id == secret['id']:
                    YandexCloudParser._retrieve_audit_data(vms_data[vm_id]['ip'], secret, server)
                    flag = True
                    break
            if not flag:
                print(f"No secret data for machine with id '{vm_id}'.")
            servers['servers'].append(server.copy())

        return servers

    @staticmethod
    def _retrieve_audit_data(ip: str, creds: dict, server_object: dict) -> None:
        """
        Connects to virtual machine via ssh, starts audit script, saves audit files, parse them and add data to
         server object
        :param ip: Server ip
        :param creds: credentials for ssh connection (Username, Key passphrase, Path of key file)
        :param server_object: Server object to fill data
        :return: None
        """
        commands = ["./audit_script"]

        console = SSHConsole(ip, creds['user'],
                             creds['pass'],
                             creds['keys_paths'])
        if not console.ok:
            return None

        # 1) Execute bash script
        output = execute_commands_on_server(console, commands)[0]
        msgs = output[0].split('\n')
        errs = output[1].split('\n')

        # 2) Analyse output
        if 'No net-tools package' in msgs:
            print(f"No net-tools installed on machine {server_object['name']} (id {server_object['id']}). Leaving 'services' segment empty")
        if 'No debsecan package' in msgs:
            print(f"No debsecan installed on machine {server_object['name']} (id {server_object['id']}). Leaving 'vulns' segment empty")

        for err in errs:
            if 'ifconfig: command not found' in err:
                print(f"No ifconfig installed on machine {server_object['name']} (id {server_object['id']}). Leaving 'ips' segment empty")
            elif 'audit_script: No such file or directory' in err:
                print(f"No audit script on machine {server_object['name']} (id {server_object['id']}). Leaving server object empty")
                return None
            elif err != '':
                print(f"Error on {server_object['name']} (id {server_object['id']}): {err}")

        if 'Audit script finished' in msgs:
            print(f"Audit script finished. Machine {server_object['name']} (id {server_object['id']}) ready to send files.")

        # 3) Saving audit files
        saved_path = pathlib.Path(os.getcwd()).joinpath(".saved/")
        if not saved_path.exists():
            try:
                os.mkdir(saved_path)
            except OSError as error:
                print(error)

        # files on server are generated by script so no problem
        # directory is created below
        data_objs = ['vulns', 'ips', 'services',
                      'packages', 'os']
        for obj in data_objs:
            retrieve_file_on_server(console, f"{obj}.txt", f".saved/{obj}.txt")

        lin_audit_parser = LinuxAuditParsers()

        # 4) Parsing saved files
        # os has header values
        with open('.saved/os.txt', 'r', encoding='utf-8') as file:
            server_object['OS_name'] = lin_audit_parser.parse('os', file.readlines())[0]['OS_name']

        for obj in data_objs:
            with open(f".saved/{obj}.txt", 'r', encoding='utf-8') as file:
                if obj == 'os':
                    continue
                try:
                    parser_data = lin_audit_parser.parse(obj, file.readlines())
                    server_object[obj] = parser_data
                except Exception:
                    print(f"Error while parsing '{obj}.txt'. Leaving '{obj}' empty for machine '{server_object['id']}'")
                    server_object[obj] = []

        # Cleaning up saved files
        [os.remove(x) for x in saved_path.iterdir()]
