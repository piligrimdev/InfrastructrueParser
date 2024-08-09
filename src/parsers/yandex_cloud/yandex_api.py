# -*- coding: utf-8 -*-
import requests


class YandexAPI:
    @staticmethod
    def handle_bad_request(resp: requests.Response) -> bool:
        if resp.ok:
            return True
        else:
            raise Exception(f'Something went wrong with {resp.request.url} request.\n {resp.reason}')

    def handle_request_exception(self, url: str, json: dict) -> requests.Response | None:
        try:
            resp = self._session.get(url, headers=self.headers, params=json)
            return resp
        except Exception as e:
            raise Exception(f'Something went wrong with {url} request connection .\n {e}')

    def __init__(self, oauth: str):
        # Getting iam
        self._oauth = oauth
        self._session = requests.session()
        iam_resp = self._session.post('https://iam.api.cloud.yandex.net/iam/v1/tokens'
                                      , json={'yandexPassportOauthToken': self._oauth})
        if YandexAPI.handle_bad_request(iam_resp):
            self._iam = iam_resp.json()['iamToken']

        self.headers = {
            'Authorization': f"Bearer {self._iam}"
        }

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

    def get_virtual_machines_list_by_folder_id(self, folder_id) -> list:
        vm_list = self.handle_request_exception(f'https://compute.api.cloud.yandex.net/compute/v1/instances',
                                      {'folderId': folder_id})
        if YandexAPI.handle_bad_request(vm_list):
            return vm_list.json()['instances']

    def get_virtual_machine_data_by_id(self, vm_id) -> dict:
        vm_info = self.handle_request_exception(f'https://compute.api.cloud.yandex.net/compute/v1/instances/{vm_id}',
                                      {})
        if YandexAPI.handle_bad_request(vm_info):
            return vm_info.json()

    def __del__(self):
        self._session.close()
        del self._oauth
        del self.headers
