# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup as BS
import html
import unicodedata
import json

file_path = 'drawio.xml'
json_template = 'templates/segment_template.json'

result = {
    'hardware': [],
    'controllers': [],
    'external_media': [],
    'shd': [],
    'telecom': [],
    'virtual_segment': []
}

with open(file_path, 'r', encoding='utf-8') as file:
    bs = BS(file, 'xml')
    #TODO read from file
    template = {
        'hardware': {'param': 'rounded', 'value': '0'},
        'controllers': {'param': 'rounded', 'value': '1'},
        'external_media': {'param': 'shape', 'value': 'cylinder3'},
        'shd': {'param': 'rhombus', 'value': ''},
        'telecom': {'param': 'shape', 'value': 'hexagon'},
        'virtual_segment': {'param': 'shape', 'value': 'cloud'}
    }

    # TODO read from file
    records = {
        'hardware': [],
        'controllers': [],
        'external_media': [],
        'shd': [],
        'telecom': [],
        'virtual_segment': []
    }

    items = bs.find_all('mxCell')
    for item in items:
        if 'style' in item.attrs.keys():
            temp = item.attrs['style'].split(';')
            style_params = dict()
            for i in temp:
                if '=' in i:
                    nigga = i.split('=')
                    style_params[nigga[0]] = nigga[1]
                else:
                    style_params[i] = ''

            for map_param in template.items():
                for param in style_params.keys():
                    if map_param[1]['param'] == param and map_param[1]['value'] == style_params[param]:
                        cooked_data = item.attrs['value'].replace('<div>', '').replace('</div>', '')
                        cooked_data = html.unescape(cooked_data)
                        cooked_data = unicodedata.normalize('NFKD', cooked_data)
                        records[map_param[0]] += [cooked_data]

    for key in records.keys():
        for record in records[key]:
            pairs = record.split(';')
            data = dict()
            for pair in pairs:
                splited = [x.strip() for x in pair.split(':')]

                if splited[1].startswith('['):
                    temp = splited[1].replace('[', '').replace(']', '')
                    temp_list = [int(x) for x in temp.split(',')]
                    splited[1] = [{'id': _id} for _id in temp_list]

                data[splited[0]] = splited[1]
            result[key] += [data]

json_result = {}

with open(json_template, 'r', encoding='utf-8') as file:
    json_template = json.load(file)
    json_result = json_template

    for key in result.keys():
        record_list = list()

        for fuck in result[key]:
            record_template = json_template['segment'][0][key][0]

            for fuck_key in fuck.keys():
                record_template[fuck_key] = fuck[fuck_key]

            record_list += [record_template]
        json_result['segment'][0][key] = record_list.copy()

with open('result.json', 'w', encoding='utf-8') as file:
    json.dump(json_result, file, ensure_ascii=False, indent=4)