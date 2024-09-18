# -*- coding: utf-8 -*-
import random

from .netbox_api.netbox_api import NetboxAPI


def create_unique_name(name: str) -> str:
    return f"{name}-{abs(hash(name)) % (10 ** 4) * random.randint(1, 100)}"


def fill_netbox(creds: dict, segment: dict) -> bool:
    netbox = NetboxAPI(creds['host'], creds['token'])

    hw = segment['hardware']  # idk
    cnt = segment['controllers']
    exm = segment['external_media']
    shd = segment['shd']
    tcm = segment['telecom']

    flag = True

    for i in list(hw):
        custom_fields = {
            'Model': i['Model'],
            'OS_name': i['OS_name'],
            'ip': i['ip'],
            'servers': i['servers'],
            'virtual_servers': i['virtual_servers'],
            'virtualization_name': i['virtualization_name']
        }
        if netbox.create_device('hardware', create_unique_name(i['name']), i['tag'],
                                serial_number=i['SN'], locations=i['locations'],
                                rack_locations=i['rack_locations'],
                                custom_fields=custom_fields):
            print(f"Created device '{i['name']}' successfully")
        else:
            flag = False

    for i in cnt:
        custom_fields = {
            'Model': i['Model'],
            'OS_name': i['OS_name'],
            'ip': i['ip']
        }
        if netbox.create_device('controller', create_unique_name(i['name']), i['tag'], role=i['type'],
                                serial_number=i['SN'], locations=i['locations'],
                                rack_locations=i['rack_locations'],
                                custom_fields=custom_fields):
            print(f"Created device '{i['name']}' successfully")
        else:
            flag = False

    for i in exm:
        if netbox.create_device('external-media', create_unique_name(i['name']), i['tag'], role=i['type'],
                                serial_number=i['SN']):
            print(f"Created device '{i['name']}' successfully")
        else:
            flag = False

    for i in shd:
        custom_fields = {
            'Model': i['model'],
            'OS_name': i['OS_name']
        }
        if netbox.create_device('shd', create_unique_name(i['name']), i['tag'], role=i['type'],
                                locations=i['locations'],
                                rack_locations=i['rack_locations'],
                                custom_fields=custom_fields):
            print(f"Created device '{i['name']}' successfully")
        else:
            flag = False

    for i in tcm:
        custom_fields = {
            'Model': i['model'],
            'OS_name': i['OS'],
            'ip': i['ip']
        }
        if netbox.create_device('telecom', create_unique_name(i['name']), i['tag'], role=i['type'],
                                serial_number=i['SN'], locations=i['locations'],
                                rack_locations=i['rack_locations'],
                                custom_fields=custom_fields):
            print(f"Created device '{i['name']}' successfully")
        else:
            flag = False

    return flag
