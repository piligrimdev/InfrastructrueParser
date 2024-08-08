# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup as BS


class ScanOVALParser:
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


def parse_scanoval(bs_obj: BS) -> list:
    parser = ScanOVALParser(bs_obj)
    return parser.prarse_vulns_table()