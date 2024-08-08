# -*- coding: utf-8 -*-

def parse_ips(ip_lines: list[str]) -> list[dict]:
    ips = []
    for index in range(0, len(ip_lines), 9):
        obj = {}
        obj['iface'] = ip_lines[index].split(':')[0]
        net = [i for i in ip_lines[index + 1].strip().split(' ') if i != '']
        obj['address'] = net[1]
        obj['netmask'] = net[3]
        mac_line = [i for i in ip_lines[index + 3].strip().split(' ') if i != '']
        if mac_line[0] == 'ether':
            obj['mac'] = mac_line[1]
        else:
            obj['mac'] = ''
        ips.append(obj.copy())
    return ips


def parse_packages(pkg_lines: list[str]) -> list[dict]:
    packages = []
    lines = [i for i in pkg_lines if i.startswith('ii')]
    for line in lines:
        data = [i for i in line.split(' ') if i != '']
        pkg = {}
        pkg['name'] = data[1]
        pkg['version'] = data[2]
        pkg['type'] = 'debian package'
        packages.append(pkg.copy())
    return packages


def parse_services(srvs_lines: list[str]) -> list[dict]:
    srvs_lines = srvs_lines[2:]
    services = []

    for line in srvs_lines:
        data = [i for i in line.split(' ') if i != '']
        obj = dict()
        obj['protocol'] = data[0]
        adr_port = data[3].split(":")
        obj['address'] = adr_port[0]
        obj['port'] = adr_port[-1]
        if data[-2] == '-':
            obj['process'] = ''
        else:
            obj['process'] = data[-2].split('/')[1]
        services.append(obj.copy())

    return services


def parse_debsecan_vulns(v_lines: list[str]) -> list[dict]:
    vulns = []
    flag = True
    for index in range(0, len(v_lines)):
        if flag:
            vuln = {}
            vuln['name'] = v_lines[index].strip()
            vuln['title'] = v_lines[index + 1].strip()
            pkg_ver_data = v_lines[index + 2].strip().split(' ')
            vuln['version'] = pkg_ver_data[1] + ' ' + pkg_ver_data[2]
            vulns.append(vuln.copy())
            flag = False
        else:
            if v_lines[index] == '\n':
                flag = True
    return vulns


def parse_os(os_lines: list[str]) -> dict:
    result = dict()

    for line in os_lines:
        key_value = line.split(': ')
        if key_value[0] == 'Operating System':
            result['OS_name'] = key_value[1]

    return result
