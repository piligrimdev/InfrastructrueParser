# -*- coding: utf-8 -*-

# Command patten yay!!
class LinuxMetaParser:
    def parse(self, lines: list[str]) -> list[dict]:
        pass


class IPParser(LinuxMetaParser):
    def parse(self, lines: list[str]) -> list[dict]:
        ips = []
        for index in range(0, len(lines), 9):
            obj = {}
            obj['iface'] = lines[index].split(':')[0]
            net = [i for i in lines[index + 1].strip().split(' ') if i != '']
            obj['address'] = net[1]
            obj['netmask'] = net[3]
            mac_line = [i for i in lines[index + 3].strip().split(' ') if i != '']
            if mac_line[0] == 'ether':
                obj['mac'] = mac_line[1]
            else:
                obj['mac'] = ''
            ips.append(obj.copy())
        return ips


class PackagesParser(LinuxMetaParser):
    def parse(self, lines: list[str]) -> list[dict]:
        packages = []
        lines = [i for i in lines if i.startswith('ii')]
        for line in lines:
            data = [i for i in line.split(' ') if i != '']
            pkg = {}
            pkg['name'] = data[1]
            pkg['version'] = data[2]
            pkg['type'] = 'debian package'
            packages.append(pkg.copy())
        return packages


class ServicesParser(LinuxMetaParser):
    def parse(self, lines: list[str]) -> list[dict]:
        srvs_lines = lines[2:]
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


class DebsecanParser(LinuxMetaParser):
    def parse(self, lines: list[str]) -> list[dict]:
        vulns = []
        flag = True
        for index in range(0, len(lines)):
            if flag:
                vuln = {}
                vuln['name'] = lines[index].strip()
                vuln['title'] = lines[index + 1].strip()
                pkg_ver_data = lines[index + 2].strip().split(' ')
                vuln['version'] = pkg_ver_data[1] + ' ' + pkg_ver_data[2]
                vulns.append(vuln.copy())
                flag = False
            else:
                if lines[index] == '\n':
                    flag = True
        return vulns


class OSParser(LinuxMetaParser):
    def parse(self, lines: list[str]) -> list[dict]:
        result = dict()

        for line in lines:
            key_value = line.split(': ')
            if key_value[0] == 'Operating System':
                result['OS_name'] = key_value[1]

        return [result]


class LinuxAuditParsers:
    def __init__(self):
        self.parse_dict = {
            'ips': IPParser(),
            'packages': PackagesParser(),
            'services': ServicesParser(),
            'vulns': DebsecanParser(),
            'os': OSParser()
        }

    def parse(self, parse_obj: str, lines: list[str]):
        if parse_obj in self.parse_dict.keys():
            return self.parse_dict[parse_obj].parse(lines)
        else:
            raise Exception(f"No parsing object with name {parse_obj}")
