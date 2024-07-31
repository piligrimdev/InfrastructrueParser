# -*- coding: utf-8 -*-
import pathlib

from bs4 import BeautifulSoup as BS
import html
import unicodedata
import json
import re


class DrawIOParser:
    def __init__(self, bs_obj: BS, figures_regocnition_template: dict):
        self.cooked_data_re = re.compile('<.*?>')
        self.bs = bs_obj
        self.template = figures_regocnition_template
        self.figures_text = dict()
        self.result = dict()
        for key in self.template['figures_recognition'].keys():
            self.figures_text[key] = []
            self.result[key] = []

    def _clean_html(self, raw_html):
        cleantext = re.sub(self.cooked_data_re, '', raw_html)
        return cleantext

    def _recognize_figures(self) -> dict:
        figures = self.bs.find_all('mxCell')
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
                            #cooked_data = figure.attrs['value'].replace('<div>', '').replace('</div>', '')
                            cooked_data = self._clean_html(figure.attrs['value'])
                            cooked_data = html.unescape(cooked_data)
                            cooked_data = unicodedata.normalize('NFKD', cooked_data)
                            self.figures_text[mapping_param[0]].append(cooked_data)
        return self.figures_text

    def store_figure_values(self) -> dict:
        self._recognize_figures()
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


def read_json(file_path: pathlib.Path) -> dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def write_to_result_json(data: dict, mapping_template: dict, segment_template: dict) -> None:
    for data_key in data.keys():
        record_list = list()

        for record in data[data_key]:
            record_template = segment_template['segment'][0][data_key][0]

            #map here
            for mapping_key in mapping_template[data_key].keys():
                record_template[mapping_key] = record[mapping_template[data_key][mapping_key]]

            record_list += [record_template]
        segment_template['segment'][0][data_key] = record_list.copy()


def parse_drawio(drawio_path: pathlib.Path, parse_template_path: pathlib.Path,
                 result_template_path: pathlib.Path) -> dict:

    drawio_file = [x for x in drawio_path.iterdir() if x.name.endswith('.xml') or x.name.endswith('.drawio')][0]
    with open(drawio_file, 'r', encoding='utf-8') as file:
        bs = BS(file, 'xml')

    parse_template = read_json(parse_template_path)

    parser = DrawIOParser(bs, parse_template)
    result = parser.store_figure_values()

    result_template = read_json(result_template_path)
    write_to_result_json(result, parse_template['figures_text_mapping'], result_template)

    return result_template
