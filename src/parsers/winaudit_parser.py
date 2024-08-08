# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup as BS, PageElement


class WinAuditParser:
    def __init__(self, bs_object: BS):
        self.bs_object = bs_object
        self.comp_name = self.bs_object.find('center').text.split(' ')[-1]

    def parse_section(self, section_name: str, map_values: dict) -> list[dict]:
        tables = self.get_tables_by_section(section_name)
        return [WinAuditParser.parse_table(table, map_values) for table in tables]

    def get_tables_by_section(self, section_start_name: str) -> list[PageElement]:
        result = []
        anchor = None

        centers = self.bs_object.find_all('center')
        for centerEl in centers:
            bEl = centerEl.findChild('b')
            if bEl is not None:
                if section_start_name in bEl.text:
                    anchor = centerEl
                    break

        if anchor is None:
            raise ValueError(f"No section named {section_start_name} founded for {self.comp_name}")

        sibling = anchor.find_next_sibling('table')
        while sibling.name != 'center':
            if sibling.name == 'table':
                result.append(sibling)
            sibling = sibling.next_sibling

        return result

    @staticmethod
    def parse_table(table: PageElement, map_values: dict) -> dict:
        result = {}
        table_data = {}

        rows = table.findChildren("tr")
        for row in rows:
            td1, td2 = row.findChildren("td")
            table_data[td1.text.strip()] = td2.text.strip()

        for item in map_values.items():
            if item[1] is None:
                result[item[0]] = ''
                continue
            result[item[0]] = table_data[item[1]]

        return result


def setup_winaudit_template(templates: dict) -> None:
    """
    Converting empty string values in non-blank templates to 'None' values
    """
    for i in templates:
        for key in i['template'].keys():
            if i['template'][key] == '' and i['type'] != 'blank':
                i['template'][key] = None


def winaudit_blank(templates: dict) -> dict:
    setup_winaudit_template(templates)

    server = dict()

    for i in templates:
        if i['type'] == 'head':
            for j in i['template'].items():
                server[j[0]] = ''
        elif i['type'] == 'list':
            server[i['section_name']] = []

    return server


def parse_winaudit(bs_objs: BS, templates: dict) -> dict:
    templates = templates['templates']
    setup_winaudit_template(templates)

    server = dict()
    parser = WinAuditParser(bs_objs)

    for i in templates:
        if i['type'] == 'head':
            server = parser.parse_section(i['html_section_name'], i['template'])[0]
            break

    for i in templates:
        if i['type'] == 'list':
            try:
                if i['section_name'] in server.keys():
                    server[i['section_name']] += parser.parse_section(i['html_section_name'], i['template'])
                else:
                    server[i['section_name']] = parser.parse_section(i['html_section_name'], i['template'])
            except ValueError as e:
                print(e)
                if i['section_name'] not in server.keys():
                    server[i['section_name']] = []
        elif i['type'] == 'blank':
            server[i['section_name']] = []

    return server
