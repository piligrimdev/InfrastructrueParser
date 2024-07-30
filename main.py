# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup as BS, PageElement
import pathlib
import json
import argparse


class WinAuditParser:
    def __init__(self, bs_object: BS):
        self.bs_object = bs_object
        self.comp_name = self.bs_object.find('center').text.split(' ')[-1]

    def parse_section(self, section_name: str, map_values: dict) -> list[dict]:
        tables = self.get_tables_by_section(section_name)
        return [self.parse_table(table, map_values) for table in tables]

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

    def parse_table(self, table: PageElement, map_values: dict) -> dict:
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


class ScanOvalParser:
    def __init__(self, bs_object: BS):
        self.bs_object = bs_object

    def prarse_vulns_table(self) -> list:
        result = []
        table = self.bs_object.find('table', {'class': 'vulnerabilitiesListTbl'})
        rows = table.findChildren('tr')

        for i in range(0, len(rows), 8):
            item = dict()
            item['version'] = ''
            item['severity'] = rows[i].findChildren('td')[1].text.split(':')[1].strip()
            item['name'] = rows[i+1].findChildren('td')[1].text
            item['title'] = rows[i+3].findChildren('td')[0].text
            result += [item]

        return result


def setup_template(templates: dict) -> None:
    for i in templates:
        for key in i['template'].keys():
            if i['template'][key] == '' and i['type'] != 'blank':
                i['template'][key] = None


def parse_scanoval(bs_obj: BS) -> list:
    parser = ScanOvalParser(bs_obj)
    return parser.prarse_vulns_table()


def parse_winaudit(bs_objs: BS, templates: dict) -> dict:
    setup_template(templates)

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


def winaudit_blank(templates: dict) -> dict:
    setup_template(templates)

    server = dict()

    for i in templates:
        if i['type'] == 'head':
            for j in i['template'].items():
                server[j[0]] = ''
        elif i['type'] == 'list':
            server[i['section_name']] = []

    return server


def main(input_dir: pathlib.Path, output_dir: pathlib.Path, template: pathlib.Path) -> None:
    templates = json.load(template.open(encoding='utf-8'))['templates']

    result = dict()
    result['servers'] = []
    server_id = 0

    dirs = [d.absolute() for d in input_dir.iterdir() if d.is_dir()]
    for c_dir in dirs:
        html_files = [f.absolute() for f in c_dir.iterdir() if f.is_file() and f.name.endswith('.html')]

        scanoval_obj: BS = None
        winAudit_obj: BS = None

        for file_name in html_files:
            with open(file_name, 'r', encoding='utf-8', errors='ignore') as file:
                bs_obj = BS(file, 'html.parser', from_encoding='utf-8')
                title = bs_obj.find('head').find('title').text

                if 'WinAudit' in title:
                    winAudit_obj = bs_obj
                elif 'Отчет по найденным уязвимостям' in title:
                    scanoval_obj = bs_obj

        if winAudit_obj is not None:
            winaudit_result = parse_winaudit(winAudit_obj, templates)
        else:
            print(f'No winaudit file founded in {c_dir}. Check file for encoding')
            winaudit_result = winaudit_blank(templates)

        if scanoval_obj is not None:
            result_scanoval = parse_scanoval(scanoval_obj)
        else:
            print(f'No scanoval file founded in {c_dir}. Check file for encoding')
            result_scanoval = []

        winaudit_result['vulns'] = result_scanoval
        winaudit_result['id'] = server_id

        result['servers'].append(winaudit_result)

        server_id += 1

    output_file = output_dir.joinpath('servers.json')
    with open(output_file.absolute(), 'w', encoding='utf-8') as file:
        json.dump(result, file, ensure_ascii=False, indent=4)
        print(f'Saved as {output_file}')


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser('WinAudit parser')

    arg_parser.add_argument('-inDir', help='Path to directory containing directoires with winaudit'
                                           ' and scanoval .html files', required=True)
    arg_parser.add_argument('-outDir', help='Path to output directory for resulting .json file',
                            required=True)
    arg_parser.add_argument('-template', help='Path to parsing template', required=True)

    args = arg_parser.parse_args()
    inputDir = pathlib.Path(args.inDir)
    outputDir = pathlib.Path(args.outDir)
    template = pathlib.Path(args.template)

    if inputDir.exists() and outputDir.exists() and template.exists() and template.is_file():
        main(inputDir, outputDir, template)
    else:
        print("Non-exsisting paths, files or invalid input")