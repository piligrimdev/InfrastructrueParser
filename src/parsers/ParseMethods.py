# -*- coding: utf-8 -*-
from typing import TextIO
import pathlib

from .winaudit_parser import *
from .scanOVAL_parser import *
from .drawIO_parser import *
from .yandexCloud_parser import *
from .vmware_cloud_director_parser import *


# Logic of this method implies it need directories as input and not actual files/data/BS objects e.t.c
def parse_local_servers(input_dir: pathlib.Path, templates: dict) -> dict:
    result = dict()
    result['servers'] = []
    server_id = 0

    dirs = [d.absolute() for d in input_dir.iterdir() if d.is_dir()]
    for c_dir in dirs:
        print(f"Parsing server {c_dir.name}")
        html_files = [f.absolute() for f in c_dir.iterdir() if f.is_file() and f.name.endswith('.html')]

        scanoval_obj = None
        winaudit_obj = None

        for file_name in html_files:
            with open(file_name, 'r', encoding='utf-8', errors='ignore') as file:
                bs_obj = BS(file, 'html.parser', from_encoding='utf-8')
                title = bs_obj.find('head').find('title').text

                if 'WinAudit' in title:
                    winaudit_obj = bs_obj
                elif 'Отчет по найденным уязвимостям' in title:
                    scanoval_obj = bs_obj

        if winaudit_obj is not None:
            print(f"Parsing winaudit file in {c_dir}")
            winaudit_result = parse_winaudit(winaudit_obj, templates)
        else:
            print(f'No winaudit file founded in {c_dir}. Check file for encoding')
            winaudit_result = winaudit_blank(templates)

        if scanoval_obj is not None:
            print(f"Parsing scanOVAl file in {c_dir}")
            result_scanoval = parse_scanoval(scanoval_obj)
        else:
            print(f'No scanoval file founded in {c_dir}. Check file for encoding')
            result_scanoval = []

        winaudit_result['vulns'] = result_scanoval
        if not c_dir.name.isnumeric():
            winaudit_result['id'] = server_id
            print(f'No id in directory ({c_dir.name}). Setting id as {server_id}')
            server_id += 1
        else:
            winaudit_result['id'] = int(c_dir.name)

        result['servers'].append(winaudit_result)
        print("")

    return result


def parse_drawio(drawio_file: TextIO, parse_template: dict,
                 result_template: dict) -> dict:

    bs = BS(drawio_file, 'xml')

    print(f"Parsing diagram {drawio_file.name}")
    parser = DrawIOParser(bs, parse_template)
    try:
        result = parser.store_figure_values()
        print(f"Diagram {drawio_file.name} parsed")
    except ValueError as e:
        print(e, 'Using Segment template as result', sep='\n')
        result = {}

    write_to_result_json(result, parse_template['figures_text_mapping'], result_template)

    return result_template


def parse_yandex_cloud_vms(cloud_creds: dict, vm_credentials: list[dict]) -> dict:
    try:
        parser = YandexCloudParser(cloud_creds['key_data_path'])
        print('Parsing Yandex Cloud virtual machines')
        folder_id = parser.get_folder_id(cloud_creds['org'], cloud_creds['cloud'],  cloud_creds['folder'])
        print(f"Folder with name '{cloud_creds['folder']}' founded")
        vms_data = parser.get_virtual_machines_ips(folder_id)
        print('Virtual machines IPs retrieved')
        result = parser.get_yacloud_server_objects(vms_data, vm_credentials)
    except Exception as e:
        print(f"Error occurred while parsing yacloud. Leaving yacloud's 'servers' empty.\n\tError: {e}")
        result = {'servers': []}
    return result


def parse_yandex_cloud_entities(cloud_creds: dict) -> dict:
    try:
        parser = YandexCloudParser(cloud_creds['key_data_path'])
        print(f"Parsing Yandex Cloud Entities")
        folder_id = parser.get_folder_id(cloud_creds['org'], cloud_creds['cloud'],  cloud_creds['folder'])
        print(f"Folder with name '{cloud_creds['folder']}' founded")
        result = parser.get_cloud_objects(folder_id)
    except Exception as e:
        print(f"Error occurred while parsing yacloud entities. Leaving 'yacloud' empty.\n\tError: {e}")
        result = dict()
    return result


def parse_vmware_cloud_director_entities(cloud_creds: dict, vdc_name: str) -> dict:
    try:
        parser = VMWareCloudDirectorAPI(cloud_creds)
        print(f"Parsing VMWare Cloud Director on address {cloud_creds['host']}")
        vdc = get_vmware_vdc_by_name(parser, vdc_name)
        if vdc is not None:
            print(f"VDC with name {vdc_name} founded")
            result = parse_vmware_vdc(parser, vdc)
        else:
            print(f"No VDC with name {vdc_name} founded")
            result = dict()
    except Exception as e:
        print(f"Error occurred while parsing VMWare Cloud Director entities. "
              f"Leaving 'vmware_cloud_director' empty.\n\tError: {e}")
        result = dict()
    return result
