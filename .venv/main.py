from bs4 import BeautifulSoup as BS, PageElement
import pathlib
import json
import argparse

class Parser:
    def __init__(self, bs_object: BS):
        self.bs_object = bs_object

    def parse_section(self, section_name: str, map_values: dict) -> list[dict]:
        tables = self.get_tables_by_section(section_name)
        return [self.parse_table(table, map_values) for table in tables]

    def get_tables_by_section(self, section_start_name: str) -> list[PageElement]:
        result = []
        anchor: PageElement

        centers = self.bs_object.find_all('center')
        for centerEl in centers:
            bEl = centerEl.findChild('b')
            if bEl is not None:
                if section_start_name in bEl.text:
                    anchor = centerEl
                    break

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

def main(inputDir: pathlib.Path, outputDir: pathlib.Path, template: pathlib.Path) -> None:
    templates = json.load(template.open(encoding='utf-8'))['templates']
    for i in templates:
        for key in i['template'].keys():
            if i['template'][key] == '' and i['type'] != 'blank':
                i['template'][key] = None

    resultJson = {'servers': []}
    serverId = 0

    htmlFiles = [f for f in inputDir.iterdir() if f.is_file() and f.name.endswith('.html')]
    for fileName in htmlFiles:
        with open(fileName.absolute(), 'r') as file:
            bsObj = BS(file, 'html.parser', from_encoding='utf-8')
            parser = Parser(bsObj)

            server = {}
            for i in templates:
                if i['type'] == 'head':
                    server = parser.parse_section(i['html_section_name'], i['template'])[0]
                    break

            for i in templates:
                if i['type'] == 'list':
                    server[i['section_name']] = parser.parse_section(i['html_section_name'], i['template'])
                elif i['type'] == 'blank':
                    server[i['section_name']] = i['template']

            server['id'] = serverId
            resultJson['servers'].append(server)
        serverId += 1

    outputDir = outputDir.joinpath('servers.json')
    with open(outputDir.absolute(), 'w', encoding='utf-8') as file:
        json.dump(resultJson, file, ensure_ascii=False, indent=4)
        print(f'Saved as {outputDir}')

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser('WinAudit parser')
    arg_parser.add_argument('inDir', help='Path to directory containing .html winaudit files')
    arg_parser.add_argument('outDir', help='Path to output directory for .json file')
    arg_parser.add_argument('template', help='Path to parsing template')

    args = arg_parser.parse_args()
    inputDir = pathlib.Path(args.inDir)
    outputDir = pathlib.Path(args.outDir)
    template = pathlib.Path(args.template)
    if inputDir.exists() and outputDir.exists() and template.exists() and template.is_file():
        main(inputDir, outputDir, template)
    else:
        print("Non-exsisting pathes or invalid input")