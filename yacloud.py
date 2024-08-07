# -*- coding: utf-8 -*-
# TODO async
import requests
import json
import paramiko
from linux_audit_parser import *

#paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)


class SSHConsole:
    def __init__(self, host: str, user: str, pw: str, p_key: str):
        self.host = host
        self.user = user
        self.pf = pw
        self.key_path = p_key

    def execute_command(self, command: str) -> list[str]:
        key = paramiko.Ed25519Key.from_private_key_file(self.key_path, self.pf)
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # idk
            ssh.connect(self.host, username=self.user, pkey=key)
            return [i.read().decode() for i in ssh.exec_command(command)[1:]]

    def retrieve_file(self, file_path: str, save_path) -> None:
        key = paramiko.Ed25519Key.from_private_key_file(self.key_path, self.pf)
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # idk
            ssh.connect(self.host, username=self.user, pkey=key)
            with ssh.open_sftp() as sftp:
                sftp.get(file_path, save_path)


class YadnexAPI:
    @staticmethod
    def handle_bad_request(resp: requests.Response) -> bool:
        if resp.status_code == 200:
            return True
        else:
            raise Exception(f'Something went wrong with {resp.request.url} request.\n {resp.reason}')

    def __init__(self, oauth: str):
        # Getting iam
        self._oauth = oauth
        self._session = requests.session()
        iam_resp = self._session.post('https://iam.api.cloud.yandex.net/iam/v1/tokens'
                                      , json={'yandexPassportOauthToken': self._oauth})
        if YadnexAPI.handle_bad_request(iam_resp):
            self._iam = iam_resp.json()['iamToken']

        self.headers = {
            'Authorization': f"Bearer {self._iam}"
        }

    def get_all_organizations_list(self) -> list:
        # TODO pagination to get all orgs
        org_resp = self._session.get(
            'https://organization-manager.api.cloud.yandex.net/organization-manager/v1/organizations',
            headers=self.headers)
        if YadnexAPI.handle_bad_request(org_resp):
            # TODO
            return org_resp.json()['organizations']

    def get_clouds_by_org_id(self, org_id: int) -> list:
        cloud_resp = requests.get('https://resource-manager.api.cloud.yandex.net/resource-manager/v1/clouds',
                                  params={'organizationId': org_id},
                                  headers=self.headers)
        if YadnexAPI.handle_bad_request(cloud_resp):
            return cloud_resp.json()['clouds']

    def get_folders_by_cloud_id(self, cloud_id: int) -> list:
        fold_resp = requests.get('https://resource-manager.api.cloud.yandex.net/resource-manager/v1/folders',
                                 params={'cloudId': cloud_id},
                                 headers=self.headers)
        if YadnexAPI.handle_bad_request(fold_resp):
            return fold_resp.json()['folders']

    def get_virtual_machines_list_by_folder_id(self, folder_id) -> list:
        vm_list = requests.get(f'https://compute.api.cloud.yandex.net/compute/v1/instances',
                               params={'folderId': folder_id},
                               headers=self.headers)
        if YadnexAPI.handle_bad_request(vm_list):
            return vm_list.json()['instances']

    def get_virtual_machine_data_by_id(self, vm_id) -> dict:
        vm_info = requests.get(f'https://compute.api.cloud.yandex.net/compute/v1/instances/{vm_id}',
                               headers=self.headers)
        if YadnexAPI.handle_bad_request(vm_info):
            return vm_info.json()


# TODO safe secrets retrieving
def parse_cloud_vms(org_name: str, cloud_name: str, folder_name: str) -> list[dict]:
    with open('', 'r', encoding='utf-8') as file:
        secrets = json.load(file)

    oauth_token = secrets['yandex_cloud']['oauth']

    yandex = YadnexAPI(oauth_token)
    orgs = yandex.get_all_organizations_list()
    org_id = ''
    for i in orgs:
        if i['name'] == org_name:
            org_id = i['id']
            break

    if org_id == '':
        raise Exception(f'No organization with name {org_name}')

    clouds = yandex.get_clouds_by_org_id(org_id)
    cloud_id = ''
    for i in clouds:
        if i['name'] == cloud_name:
            cloud_id = i['id']
            break

    if cloud_id == '':
        raise Exception(f'No cloud with name {cloud_name}')

    folders = yandex.get_folders_by_cloud_id(cloud_id)
    folder_id = ''
    for i in folders:
        if i['name'] == folder_name:
            folder_id = i['id']
            break

    if folder_id == '':
        raise Exception(f'No folder with name {folder_name}')

    vms = yandex.get_virtual_machines_list_by_folder_id(folder_id)
    if len(vms) == 0:
        print(f'No virtual machines in folder {folder_name}')
        return

    vm_ips = dict()
    for i in vms:
        data = yandex.get_virtual_machine_data_by_id(i['id'])
        # TODO what?
        for network_interface in data['networkInterfaces']:
            if 'address' in network_interface['primaryV4Address']['oneToOneNat'].keys():
                vm_ips[i['id']] = network_interface['primaryV4Address']['oneToOneNat']['address']
            else:
                print(f"Machine's '{data['name']}' net interface with index '{network_interface['index']}'"
                      f" has no public ip to connect.\n\tVM status: '{data['status']}'\n\t"
                      f"Net interface subnet id: '{network_interface['subnetId']}'")

    servers = []

    for i in vm_ips.keys():
        for j in secrets['virtual_machines']:
            if i == j['id']:
                creds = {'pass': j['pass'], 'keys_paths': j['keys_paths']}
                server = retrieve_audit_data(vm_ips[i], '', creds, i, 'placeholder')
                # TODO add server header values
                servers.append(server.copy())

    return servers


def execute_commands_on_server(console: SSHConsole, commands: list[str]):
    output = []
    try:
        for com in commands:
            output.append(tuple(console.execute_command(com)))
    except Exception as e:
        print(e)
    finally:
        return output


def retrieve_file_on_server(console: SSHConsole, file_on_server: str, path_to_save: str) -> None:
    try:
        console.retrieve_file(file_on_server, path_to_save)
    except Exception as e:
        print(e)


def retrieve_audit_data(ip: str, user: str, creds: dict, vm_id: int, vm_name: str) -> dict:
    cmnds = ["./audit_script"]

    console = SSHConsole(ip, user,
                         creds['pass'],
                         creds['keys_paths'])

    output = execute_commands_on_server(console, cmnds)[0]
    msgs = output[0].split('\n')
    errs = output[1].split('\n')

    if 'No net-tools package' in msgs:
        print(f"No net-tools installed on machine {0} (id {0}). Leaving 'services' segment empty")
    if 'No debsecan package' in msgs:
        print(f"No debsecan installed on machine {0} (id {0}). Leaving 'vulns' segment empty")
    for err in errs:
        if 'ifconfig: command not found' in err:
            print(f"No ifconfig installed on machine {0} (id {0}). Leaving 'ips' segment empty")
    if 'Audit script finished' in msgs:
        print(f"Audit script finished. Machine {0} ready to send files.")

    retrieve_file_on_server(console, 'vulns.txt', 'saved/vulns.txt')
    retrieve_file_on_server(console, 'ips.txt', 'saved/ips.txt')
    retrieve_file_on_server(console, 'services.txt', 'saved/services.txt')
    retrieve_file_on_server(console, 'packages.txt', 'saved/packages.txt')

    server_obj = {}
    with open('saved/ips.txt', 'r', encoding='utf-8') as file:
        lines = file.readlines()
        server_obj['ips'] = parse_ips(lines)
    with open('saved/vulns.txt', 'r', encoding='utf-8') as file:
        lines = file.readlines()
        server_obj['vulns'] = parse_debsecan_vulns(lines)
    with open('saved/services.txt', 'r', encoding='utf-8') as file:
        lines = file.readlines()
        server_obj['services'] = parse_services(lines)
    with open('saved/packages.txt', 'r', encoding='utf-8') as file:
        lines = file.readlines()
        server_obj['packages'] = parse_packages(lines)

    return server_obj


parse_cloud_vms('', '', '')