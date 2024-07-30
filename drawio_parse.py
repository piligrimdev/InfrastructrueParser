# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup as BS
import html
import unicodedata
import json


class DrawIOParser:
    def __init__(self, bs_obj: BS, figures_regocnition_template: dict):
        self.bs = bs_obj
        self.template = figures_regocnition_template
        self.figures_text = dict()
        self.result = dict()
        for key in self.template['figures_recognition'].keys():
            self.figures_text[key] = []
            self.result[key] = []



    def recognize_figures(self) -> dict:
        figures = bs.find_all('mxCell')
        #retrive style parameters
        for figure in figures:
            if 'style' in figure.attrs.keys():
                attrs = figure.attrs['style'].split(';')
                style_params = dict()
                for attr in attrs:
                    if '=' in attr:
                        key_value_pair = attr.split('=')
                        style_params[key_value_pair[0]] = key_value_pair[1]
                    else:
                        style_params[attr] = ''

                #Map figures to json entries
                for mapping_param in self.template['figures_recognition'].items():
                    for style_param in style_params.keys():
                        #if style parameter and it's value equals to json template
                        if (mapping_param[1]['param'] == style_param
                                and mapping_param[1]['value'] == style_params[style_param]):
                            #delete formatting, html escape chars and unicode chars from figure text
                            cooked_data = figure.attrs['value'].replace('<div>', '').replace('</div>', '')
                            cooked_data = html.unescape(cooked_data)
                            cooked_data = unicodedata.normalize('NFKD', cooked_data)
                            self.figures_text[mapping_param[0]].append(cooked_data)
        return self.figures_text

    def store_figure_values(self) -> dict:
        self.result = dict()
        for key in self.figures_text.keys():
            for figure_text in self.figures_text[key]:
                pairs = figure_text.split(';')
                data = dict()

                for pair in pairs:
                    splited = [x.strip() for x in pair.split(':')]

                    #special case for [] list of server ids for hardware figure
                    if splited[1].startswith('['):
                        unbracketed = splited[1].replace('[', '').replace(']', '')
                        id_list = [int(x) for x in unbracketed.split(',')]
                        splited[1] = [{'id': _id} for _id in id_list]
                    data[splited[0]] = splited[1]

                self.result[key].append(data)
        return self.result


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
    #TODO read template from file

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