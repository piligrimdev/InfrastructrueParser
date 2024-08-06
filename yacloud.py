# -*- coding: utf-8 -*-
# TODO async
import requests
import json
import paramiko

#paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)

class SSHConsole:
    def __init__(self, host: str, user: str, pw: str, p_key: str):
        self.connection = paramiko.SSHClient()
        self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # idk
        lol = paramiko.Ed25519Key.from_private_key_file(p_key, pw)
        self.connection.connect(host, username=user, pkey=lol)

    def execute_command(self, command: str) -> tuple:
        # hello
        return self.connection.exec_command(command)

    def close(self):
        self.connection.close()



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

# # get network id
# net_resp = requests.get('https://vpc.api.cloud.yandex.net/vpc/v1/networks',
#                          params={'folderId': fold_id},
#                          headers=headers12)
# #print(net_resp.json())
# net_id = ''
#
# # get network objects
# #
# # net_data = requests.get(f'https://vpc.api.cloud.yandex.net/vpc/v1/networks/{net_id}',
# #                          headers=headers12)
# # print(net_data.json())
#
# net_data = requests.get(f'https://vpc.api.cloud.yandex.net/vpc/v1/networks/{net_id}/subnets',
#                          headers=headers12)
# #print(json.dumps(net_data.json(), indent=4))
# subnet_id = ''
# subnet_used_addresses = requests.get(f'https://vpc.api.cloud.yandex.net/vpc/v1/subnets/{subnet_id}/addresses',
#                          headers=headers12)
# #print(json.dumps(subnet_used_addresses.json(), indent=4))


# TODO safe secrets retrieving
def parse_cloud_vms(org_name: str, cloud_name: str, folder_name: str):
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

    vm_ips = list()
    for i in vms:
        data = yandex.get_virtual_machine_data_by_id(i['id'])
        # TODO what?
        for network_interface in data['networkInterfaces']:
            if 'address' in network_interface['primaryV4Address']['oneToOneNat'].keys():
                vm_ips.append(network_interface['primaryV4Address']['oneToOneNat']['address'])
            else:
                print(f"Machine's '{data['name']}' net interface with index '{network_interface['index']}'"
                      f" has no public ip to connect.\n\tVM status: '{data['status']}'\n\t"
                      f"Net interface subnet id: '{network_interface['subnetId']}'")

def execute_commands_on_ip(ip: str, cred_path: str, commands: list[str]) -> list[str]:
    with open(cred_path, 'r') as file:
        creds = json.load(file)
    console = SSHConsole(ip, creds['user'],
                         creds['passphrase'],
                         creds['path_to_ssh_key'])
    for com in commands:
        try:
            t = console.execute_command(com)
            print(t[1].read().decode())
        except Exception as e:
            print(e)
        finally:
            console.close()

#parse_cloud_vms('organization-piligrimvstheworld', 'cloud-piligrimvstheworld', 'default')
