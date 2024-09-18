# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup as BS
import html
import unicodedata
import re


class DrawIOParser:
    def __init__(self, bs_obj: BS, figures_recognition_template: dict):
        self.html_tags_re = re.compile('<.*?>')

        self.figures_text_re \
            = re.compile(r"^([а-яА-ЯёЁ\w\-\_\@\s]+:\s*(([а-яА-ЯёЁ\w\-\_\@\s]+)|(\[([0-9]+,*)+\]))\s*;)+$")
        self.bs = bs_obj
        self.template = figures_recognition_template
        self.figures_text = dict()  # dict for string values for each figure of each figure type
        self.result = dict()        # result dict for list for each figure of each figure type
        for key in self.template['figures_recognition'].keys():
            self.figures_text[key] = []
            self.result[key] = []

    def _cook_data(self, raw_html):
        # delete formatting, html escape chars and unicode chars from figure text
        data = html.unescape(raw_html)
        data = unicodedata.normalize('NFKD', data)
        data = re.sub(self.html_tags_re, '', data)
        return data.strip()

    def _recognize_figures(self) -> dict:
        figures = self.bs.find_all('mxCell')

        # retrieve style parameters
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

                # map figures to json entries
                for mapping_param in self.template['figures_recognition'].items():
                    for style_param in style_params.keys():
                        # if style parameter and it's value equals to json template
                        if (mapping_param[1]['param'] == style_param
                                and mapping_param[1]['value'] == style_params[style_param]):
                            cooked_data = self._cook_data(figure.attrs['value'])

                            if not bool(self.figures_text_re.fullmatch(cooked_data)):
                                raise ValueError(f'Invalid data in {mapping_param[0]} (id: {figure.attrs['id']})'
                                                 f' text. Check figures text formating')

                            self.figures_text[mapping_param[0]].append(cooked_data)
        return self.figures_text

    def store_figure_values(self) -> dict:
        self._recognize_figures()

        # check lists of every figure values
        for key in self.figures_text.keys():
            for figure_text in self.figures_text[key]:
                # separate key-value pairs
                pairs = figure_text.split(';')[:-1]
                data = dict()

                # map key and value to dict
                for pair in pairs:
                    splited = [x.strip() for x in pair.split(':')]

                    # special case for [] list of server ids for hardware figure
                    if splited[1].startswith('['):
                        raw_ids = splited[1].replace('[', '').replace(']', '').split(',')

                        # because [1,2,] is acceptable by regex
                        if not raw_ids[-1].isnumeric():
                            raw_ids = raw_ids[:-1]

                        id_list = [int(x) for x in raw_ids]
                        splited[1] = [{'id': _id} for _id in id_list]
                    data[splited[0]] = splited[1]

                self.result[key].append(data.copy())
        return self.result


def write_to_result_json(data: dict, mapping_template: dict, segment_template: dict) -> None:
    for data_key in data.keys():
        record_list = list()

        for record in data[data_key]:
            record_template = segment_template['segment'][0][data_key][0]

            #map here
            for mapping_key in mapping_template[data_key].keys():
                if mapping_template[data_key][mapping_key] not in record.keys():
                    print(f"No {mapping_template[data_key][mapping_key]} key in object {record}."
                          f" {mapping_template[data_key][mapping_key]} value set to default")
                else:
                    record_template[mapping_key] = record[mapping_template[data_key][mapping_key]]

            record_list.append(record_template.copy())
        segment_template['segment'][0][data_key] = record_list.copy()