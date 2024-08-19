# -*- coding: utf-8 -*-
from .vmware_cloud.vmware_cloud_director_api import *


def get_vmware_vdc_by_name(parser: VMWareCloudDirectorAPI, name: str) -> dict | None:
    vdcs = parser.get_vdc_list()
    if isinstance(vdcs, list):
        for i in vdcs:
            if i['OrgVdcRecord']['name'] == name:
                return i['OrgVdcRecord']
    else:
        if vdcs['OrgVdcRecord']['name'] == name:
            return vdcs['OrgVdcRecord']
    return None


def parse_vmware_vdc(parser: VMWareCloudDirectorAPI, org_vdc_record: dict) -> dict:
    vdc_data = parser.get_vdc_data(org_vdc_record['href'])
    print("Retrieved general VDC data")

    vdc_data['Vdc']['ResourceEntities'] = parser.get_vdc_resources(vdc_data)
    print("Retrieved VDC Resource Entities")
    vdc_data['Vdc']['AvailableNetworks'] = parser.get_vdc_networks(vdc_data)
    print("Retrieved VDC Available Networks")
    vdc_data['Vdc']['Capabilities'] = parser.get_vdc_capabilities(vdc_data)
    print("Retrieved VDC Capabilities")
    vdc_data['Vdc']['VdcStorageProfiles'] = parser.get_vdc_storage_profile(vdc_data)
    print("Retrieved VDC Storage Profiles")

    return vdc_data
