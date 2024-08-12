# -*- coding: utf-8 -*-
from typing import TextIO
import pathlib

from .winaudit_parser import *
from .scanOVAL_parser import *
from .drawIO_parser import *
from .yandexCloud_parser import *


# Logic of this method implies it need directories as input and not actual files/data/BS objects e.t.c
def parse_local_servers(input_dir: pathlib.Path, templates: dict) -> dict:
    result = dict()
    result['servers'] = []
    server_id = 0

    dirs = [d.absolute() for d in input_dir.iterdir() if d.is_dir()]
    for c_dir in dirs:
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
            winaudit_result = parse_winaudit(winaudit_obj, templates)
        else:
            print(f'No winaudit file founded in {c_dir}. Check file for encoding')
            winaudit_result = winaudit_blank(templates)

        if scanoval_obj is not None:
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

    return result


def parse_drawio(drawio_file: TextIO, parse_template: dict,
                 result_template: dict) -> dict:

    bs = BS(drawio_file, 'xml')

    parser = DrawIOParser(bs, parse_template)
    try:
        result = parser.store_figure_values()
    except ValueError as e:
        print(e, 'Using Segment template as result', sep='\n')
        result = {}

    write_to_result_json(result, parse_template['figures_text_mapping'], result_template)

    return result_template


def parse_yandex_cloud_vms(cloud_path: dict, credentials: dict) -> dict:
    result = dict()
    try:
        parser = YandexCloudParser(credentials['yandex_cloud']['oauth'])
        vms_data = parser.get_virtual_machines_ips(cloud_path['org'], cloud_path['cloud'],  cloud_path['folder'])
        result = parser.get_yacloud_server_objects(vms_data, credentials['virtual_machines'])
    except Exception as e:
        print(f"Error occured while parsing yandex cloud. Leaving servers empty.\n\tError: {e}")
        result = {'servers': []}
    return result


def parse_yandex_cloud_entities(cloud_path: dict, credentials: dict) -> dict:
    parser = YandexCloudParser(credentials['yandex_cloud']['oauth'])
    return parser.get_cloud_entities(cloud_path['org'], cloud_path['cloud'],  cloud_path['folder'])