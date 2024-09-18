# -*- coding: utf-8 -*-
import json
import requests
import time
import jwt
import cryptography


class YandexAPI:
    @staticmethod
    def handle_bad_request(resp: requests.Response) -> bool:
        if not resp.ok:
            raise Exception(f'Something went wrong with {resp.request.url} request.\nReason: {resp.reason}')
        return True

    def handle_request_exception(self, url: str, json: dict) -> requests.Response | None:
        try:
            resp = self._session.get(url, headers=self.headers, params=json)
            return resp
        except Exception as e:
            raise Exception(f'Something went wrong with {url} request connection .\n {e}')

    def __init__(self, key_path: str):
        self._session = requests.session()
        self.headers = {}

        # src: yacloud docs
        with open(key_path, 'r') as f:
            obj = f.read()
            obj = json.loads(obj)
            private_key = obj['private_key']
            key_id = obj['key_id']
            service_account_id = obj['service_account_id']

        now = int(time.time())
        payload = {
            'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
            'iss': service_account_id,
            'iat': now,
            'exp': now + 3600
        }

        encoded_token = jwt.encode(
            payload,
            private_key,
            algorithm='PS256',
            headers={'kid': key_id}
        )

        iam_resp = self._session.post('https://iam.api.cloud.yandex.net/iam/v1/tokens'
                                      , json={'jwt': encoded_token})

        if YandexAPI.handle_bad_request(iam_resp):
            iam = iam_resp.json()['iamToken']

        self.headers['Authorization'] = f"Bearer {iam}"

    def get_all_organizations_list(self) -> list:
        # TODO pagination to get all orgs
        org_resp = self.handle_request_exception('https://organization-manager.api.cloud.yandex.net/organization-manager/v1/organizations', {})
        if YandexAPI.handle_bad_request(org_resp):
            return org_resp.json()['organizations']

    def get_clouds_by_org_id(self, org_id: int) -> list:
        cloud_resp = self.handle_request_exception('https://resource-manager.api.cloud.yandex.net/resource-manager/v1/clouds',
                                      {'organizationId': org_id})
        if YandexAPI.handle_bad_request(cloud_resp):
            return cloud_resp.json()['clouds']

    def get_folders_by_cloud_id(self, cloud_id: int) -> list:
        fold_resp = self.handle_request_exception('https://resource-manager.api.cloud.yandex.net/resource-manager/v1/folders',
                                      {'cloudId': cloud_id})
        if YandexAPI.handle_bad_request(fold_resp):
            return fold_resp.json()['folders']

    def get_virtual_machines_list_by_folder_id(self, folder_id, page_token: str = None) -> list:
        return self._get_all_list_objects(f'https://compute.api.cloud.yandex.net/compute/v1/instances',
                                          {'folderId': folder_id, 'pageSize': 1000}, 'instances')

    def get_virtual_machine_data_by_id(self, vm_id) -> dict:
        vm_info = self.handle_request_exception(f'https://compute.api.cloud.yandex.net/compute/v1/instances/{vm_id}',
                                      {})
        if YandexAPI.handle_bad_request(vm_info):
            return vm_info.json()

    def get_loadbalancer_data_by_folder_id(self, folder_id, page_token: str = None) -> list:
        return self._get_all_list_objects(f'https://alb.api.cloud.yandex.net/apploadbalancer/v1/loadBalancers',
                                          {'folderId': folder_id, 'pageSize': 1000}, 'loadBalancers')

    def get_dns_zones_by_folder_id(self, folder_id: str) -> list:
        return self._get_all_list_objects(f'https://dns.api.cloud.yandex.net/dns/v1/zones',
                                          {'folderId': folder_id, 'pageSize': 1000}, 'dnsZones')

    def get_kubernets_clusters_by_folder_id(self, folder_id: str) -> list:
        return self._get_all_list_objects(f'https://mks.api.cloud.yandex.net/managed-kubernetes/v1/clusters',
                                          {'folderId': folder_id, 'pageSize': 1000}, 'clusters')

    def get_db_clusters_by_folder_id(self, folder_id: str, db_name: str) -> list:
        return self._get_all_list_objects(f'https://mdb.api.cloud.yandex.net/managed-{db_name}/v1/clusters',
                                          {'folderId': folder_id, 'pageSize': 1000}, 'clusters')

    def get_dbs_by_cluster_id(self, cluster_id: str, db_name: str) -> list:
        return self._get_all_list_objects(f'https://mdb.api.cloud.yandex.net/managed-{db_name}/v1/clusters/{cluster_id}/databases',
                                          {'pageSize': 1000}, 'databases')

    def get_storage_buckets_by_folder_id(self, folder_id: str) -> list:
        return self._get_all_list_objects(f'https://storage.api.cloud.yandex.net/storage/v1/buckets',
                                          {'folderId': folder_id}, 'buckets')

    def _get_all_list_objects(self, url: str, params: dict,
                              list_name: str, page_token: str = None) -> list:
        if page_token is not None:
            params['page_token'] = page_token
        list_part = self.handle_request_exception(url, params)

        try:
            YandexAPI.handle_bad_request(list_part)
        except Exception as e:
            print(e)
            return []

        js = list_part.json()
        if 'nextPageToken' in js.keys():
            js[list_name].append(self._get_all_list_objects(url, params, list_name, js['nextPageToken']))
        if len(js) == 0:
            return []
        return js[list_name]

    def __del__(self):
        self._session.close()
        del self._session
        del self.headers
