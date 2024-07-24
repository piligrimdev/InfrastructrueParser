from bs4 import BeautifulSoup as BS, PageElement
import os


def get_tables_by_section(bsObj: BS, section_start_name: str) -> list[PageElement]:
    result = []
    centers = bsObj.find_all('center')
    anchor: PageElement

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

def parse_overview(bsObj: BS, mId: int) -> dict:
    result = {'name': '', 'OS_name': '', 'tag': '','id': mId}

    rowsPassed = 0
    table = get_tables_by_section(bsObj, 'Обзор системы')[0]
    rows = table.findChildren('tr')

    for row in rows:
        td1, td2 = row.findChildren("td")
        if td1.text == 'Computer Name':
            result['name'] = td2.text
            rowsPassed += 1
        elif td1.text == 'Operating System':
            result['OS_name'] = td2.text
            rowsPassed += 1

        if rowsPassed == 2:
            break

    return result

def parse_procceses(bsObj: BS) -> list[dict]:
    result = []
    tables = get_tables_by_section(bsObj, 'Open Ports')

    for table in tables:
        rows = table.findChildren("tr")

        rowsPassed = 0
        procces = {"address": "",
                   "port": 0,
                   "protocol": "",
                   "process": ""}

        for row in rows:
            td1, td2 = row.findChildren("td")
            if td1.text == 'Port Protocol':
                procces['protocol'] = td2.text
                rowsPassed += 1
            elif td1.text == 'Local Address':
                procces['address'] = td2.text
                rowsPassed += 1
            elif td1.text == 'Local Port':
                procces['port'] = td2.text
                rowsPassed += 1
            elif td1.text == 'Service Name':
                procces['process'] = td2.text
                rowsPassed += 1
            if rowsPassed == 4:
                result.append(procces)
                break

    return result


fileName = 'COMPUTER-249.html'

with open(fileName, 'r') as file:
    bsObj = BS(file, 'html.parser')

    overview = parse_overview(bsObj, 0)
    print(overview)
    procces1 = parse_procceses(bsObj)
    print(*procces1, sep='\n')