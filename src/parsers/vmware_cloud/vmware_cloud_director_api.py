# -*- coding: utf-8 -*-
import xmltodict
import base64
import requests


class VMWareCloudDirectorAPI:

    @staticmethod
    def _handle_bad_request(resp: requests.Response) -> bool:
        if not resp.ok:
            raise Exception(f'Something went wrong with {resp.request.url} request.\nReason: {resp.reason}')
        return True

    def _warp_get_request(self, href: str) -> dict:
        # todo add try-except
        resp = requests.get(href, headers=self.headers)
        if VMWareCloudDirectorAPI._handle_bad_request(resp):
            return xmltodict.parse(resp.content, attr_prefix='', cdata_key='')

    def __init__(self, credentials: dict):
        # get version
        self.host = credentials['host']

        api_vers_resp = requests.get(f'{self.host}/api/versions')
        resp_json = xmltodict.parse(api_vers_resp.content)
        latest_ver = resp_json['SupportedVersions']["VersionInfo"][-1]['Version']
        login_url = resp_json['SupportedVersions']["VersionInfo"][-1]['LoginUrl']

        # get token
        userpass = f"{credentials['user']}@{credentials['org']}:{credentials['password']}"
        encoded_userpass = base64.b64encode(userpass.encode()).decode()

        self.headers = {"Authorization": f"Basic {encoded_userpass}",
                        'Accept': f'application/*;version={latest_ver}'}

        auth_resp = requests.post(login_url, headers=self.headers)
        if VMWareCloudDirectorAPI._handle_bad_request(auth_resp):
            token = auth_resp.headers['x-vmware-vcloud-access-token']

        self.headers['Authorization'] = f'Bearer {token}'

    def get_vdc_list(self) -> list[dict[str, list | dict]] | dict[str, list | dict]:
        return self._warp_get_request \
            ('https://vcloud-ix.itglobal.com/api/query?type=orgVdc')['QueryResultRecords']

    def get_vdc_data(self, vdc_href: str) -> dict:
        return self._warp_get_request(vdc_href)

    def get_vdc_resources(self, vdc_object: dict) -> dict[str, list[dict]]:
        result = {}
        resources = vdc_object['Vdc']['ResourceEntities']['ResourceEntity']
        for i in resources:
            data = self._warp_get_request(i['href'])
            if i['type'] in result.keys():
                result[i['type']].append(data)
            else:
                result[i['type']] = [data]
        return result

    def get_vdc_networks(self, vdc_object):
        result = {'Networks': []}
        networks = vdc_object['Vdc']['AvailableNetworks']['Network']
        for i in networks:
            data = self._warp_get_request(i['href'])
            result['Networks'].append(data)
        return result

    def get_vdc_capabilities(self, vdc_object):
        result = {'SupportedHardwareVersions': []}
        networks = vdc_object['Vdc']['Capabilities']['SupportedHardwareVersions']['SupportedHardwareVersion']
        for i in networks:
            data = self._warp_get_request(i['href'])
            result['SupportedHardwareVersions'].append(data)
        return result

    def get_vdc_storage_profile(self, vdc_object):
        result = {'VdcStorageProfiles': []}
        networks = vdc_object['Vdc']['VdcStorageProfiles']['VdcStorageProfile']
        for i in networks:
            data = self._warp_get_request(i['href'])
            result['VdcStorageProfiles'].append(data)
        return result
