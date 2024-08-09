# -*- coding: utf-8 -*-
from .yandex_cloud.yandex_api import *
from .linux_remote_control.ssh_console import *
from .linux_audit_parsers import *
import os
import pathlib


class YandexCloudParser:
    def __init__(self, oauth: str):
        self.api = YandexAPI(oauth)
        self.server_placeholder = {
            "name": "", "id": "", "tag": "", "OS_name": "",
            "vulns": [], "ips": [], "services": [], "packages": []
        }

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

                    print(f"Machine's '{data['name']}' (id '{machine['id']}')"
                          f" has no public ip to connect.\n\tVM status: '{data['status']}'\n\t"
                          f"Net interface subnet id: '{network_interface['subnetId']}'")

        return vm_data

    def get_yacloud_server_objects(self, vms_data: dict, secrets: list[dict]) -> dict:
        servers = {'servers': []}

        for vm_id in vms_data.keys():
            if vms_data[vm_id]['ip'] == '':
                servers['servers'].append(self.server_placeholder.copy())
                continue
            server = {}
            for secret in secrets:
                if vm_id == secret['id']:
                    creds = {'pass': secret['pass'], 'keys_paths': secret['keys_paths']}

                    server = (self._retrieve_audit_data(vms_data[vm_id]['ip'],
                                                        secret['user'], creds, vm_id,
                                                        vms_data[vm_id]['name']))
                    break
            if len(server) == 0:
                print(f"No secret data for machine with id '{vm_id}'.")
                server = self.server_placeholder.copy()
            servers['servers'].append(server.copy())

        return servers

    def _retrieve_audit_data(self, ip: str, user: str, creds: dict, vm_id: int, vm_name: str) -> dict:
        commands = ["./audit_script"]

        console = SSHConsole(ip, user,
                             creds['pass'],
                             creds['keys_paths'])
        if not console.ok:
            return self.server_placeholder.copy()

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
            elif 'audit_script: No such file or directory' in err:
                print(f"No audit script on machine {vm_name} (id {vm_id}). Leaving server object empty")
                return self.server_placeholder.copy()
            elif err != '':
                print(f"Error on  {vm_name} (id {vm_id}): {err}")

        if 'Audit script finished' in msgs:
            print(f"Audit script finished. Machine {vm_name} (id {vm_id}) ready to send files.")

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

        # os is exception bcs has header values
        with open('.saved/os.txt', 'r', encoding='utf-8') as file:
            server = lin_audit_parser.parse('os', file.readlines())[0]
            server['name'] = vm_name
            server['id'] = vm_id

        for obj in data_objs:
            with open(f".saved/{obj}.txt", 'r', encoding='utf-8') as file:
                if obj == 'os':
                    continue
                try:
                    parser_data = lin_audit_parser.parse(obj, file.readlines())
                    server[obj] = parser_data
                except Exception:
                    print(f"Error while parsing '{obj}.txt'. Leaving '{obj}' empty for machine '{vm_id}'")
                    server[obj] = []

        [os.remove(x) for x in saved_path.iterdir()]

        return server
