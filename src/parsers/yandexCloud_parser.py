# -*- coding: utf-8 -*-
from .yandex_cloud.yandex_api import *
from .linux_remote_control.SSHConsole import *
from .linux_audit_parsers import *


class YandexCloudParser:
    def __init__(self, oauth: str):
        self.api = YandexAPI(oauth)

    def get_virtual_machines_ips(self, org_name: str, cloud_name: str, folder_name: str) -> dict:
        # Getting access to net data
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

        # Get virtual machines list
        v_machines = self.api.get_virtual_machines_list_by_folder_id(folder_id)
        if len(v_machines) == 0:
            print(f'No virtual machines in folder {folder_name}')
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

                    print(f"Machine's '{data['name']}' net interface with index '{network_interface['index']}'"
                          f" has no public ip to connect.\n\tVM status: '{data['status']}'\n\t"
                          f"Net interface subnet id: '{network_interface['subnetId']}'")

        return vm_data

    @staticmethod
    def get_yacloud_server_objects(vms_data: dict, secrets: list[dict]) -> dict:
        servers = {'servers': []}

        for vm_id in vms_data.keys():
            for secret in secrets:
                if vm_id == secret['id']:
                    creds = {'pass': secret['pass'], 'keys_paths': secret['keys_paths']}
                    server = (YandexCloudParser.
                              _retrieve_audit_data(vms_data[vm_id]['ip'],
                                                   secret['user'], creds, vm_id,
                                                   vms_data[vm_id]['name']))
                    servers['servers'].append(server.copy())

        return servers

    @staticmethod
    def _retrieve_audit_data(ip: str, user: str, creds: dict, vm_id: int, vm_name: str) -> dict:
        commands = ["./audit_script"]

        console = SSHConsole(ip, user,
                             creds['pass'],
                             creds['keys_paths'])

        output = execute_commands_on_server(console, commands)[0]
        msgs = output[0].split('\n')
        errs = output[1].split('\n')

        if 'No net-tools package' in msgs:
            print(f"No net-tools installed on machine {vm_name} (id {vm_id}). Leaving 'services' segment empty")
        if 'No debsecan package' in msgs:
            print(f"No debsecan installed on machine {vm_name} (id {vm_id}). Leaving 'vulns' segment empty")
        for err in errs:
            if 'ifconfig: command not found' in err:
                print(f"No ifconfig installed on machine {vm_name} (id {vm_id}). Leaving 'ips' segment empty")
            else:
                print(f"Error on  {vm_name} (id {vm_id}): {err}")
        if 'Audit script finished' in msgs:
            print(f"Audit script finished. Machine {vm_name} (id {vm_id}) ready to send files.")

        data_files = ['vulns.txt', 'ips.txt', 'services.txt',
                      'packages.txt', 'os.txt']
        for file in data_files:
            retrieve_file_on_server(console, file, f"saved/{file}")

        with open('saved/os.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()
            server = parse_os(lines)
            server['name'] = vm_name
            server['id'] = vm_id
        with open('saved/packages.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()
            server['packages'] = parse_packages(lines)
        with open('saved/ips.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()
            server['ips'] = parse_ips(lines)
        with open('saved/vulns.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()
            server['vulns'] = parse_debsecan_vulns(lines)
        with open('saved/services.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()
            server['services'] = parse_services(lines)
        with open('saved/packages.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()
            server['packages'] = parse_packages(lines)

        return server
