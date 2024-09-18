# -*- coding: utf-8 -*-
import argparse
import sys
from parsers.utils.format_output import AutoIndent
from parsers.ParseMethods import *
from parsers.utils.general import *
from netbox.netbox_upload_methods import *


def main(input_dir: pathlib.Path, output_dir: pathlib.Path,
         servers_template_path: pathlib.Path, drawio_template_path: pathlib.Path,
         result_template_path: pathlib.Path, credentials: dict = None, parseYandexCloudEnt: bool = False,
         parseYandexCloudVMs: bool = False, parseVMWareCloudEnt: bool = False, uploadNB: bool = False) -> None:

    # handle bad json file
    result_template = read_json(result_template_path)

    print('-' * 40)
    drawio_template = read_json(drawio_template_path)
    drawio_file = [x for x in input_dir.iterdir() if x.name.endswith('.xml') or x.name.endswith('.drawio')]
    if len(drawio_file) == 0:
        print(f"No drawio file founded in '{input_dir}'. Using segment template instead.")
        segment = result_template
    else:
        with open(drawio_file[0], 'r', encoding='utf-8') as file:
            segment = parse_drawio(file, drawio_template, result_template)

    print('-' * 40)
    servers_template = read_json(servers_template_path)
    local_servers = parse_local_servers(input_dir, servers_template)

    if parseYandexCloudEnt:
        print('-' * 40)
        yacloud_objects = parse_yandex_cloud_entities(credentials["yacloud"])
    else:
        yacloud_objects = {}

    if parseYandexCloudVMs:
        print('-' * 40)
        yacloud_servers = parse_yandex_cloud_vms(credentials["yacloud"], credentials["virtual_machines"])
    else:
        yacloud_servers = {'servers': []}

    if parseVMWareCloudEnt:
        print('-' * 40)
        vmware_objects = parse_vmware_cloud_director_entities(credentials["vmware"], credentials["vmware"]['vdc'])
    else:
        vmware_objects = {}

    segment['segment'][0]['servers'] = {'servers': local_servers['servers'] + yacloud_servers['servers']}
    segment['yacloud'] = yacloud_objects
    segment['vmware_cloud_director'] = vmware_objects

    print('-' * 40)
    output_file = output_dir.joinpath('result.json')
    with open(output_file.absolute(), 'w', encoding='utf-8') as file:
        json.dump(segment, file, ensure_ascii=False, indent=4)
        print(f'Saved as {output_file}')

    if uploadNB:
        print('-' * 40)
        fill_netbox(credentials['netbox'], segment['segment'][0])


if __name__ == '__main__':
    sys.stdout = AutoIndent(sys.stdout)
    arg_parser = argparse.ArgumentParser('WinAudit parser')

    required = arg_parser.add_argument_group('required arguments')
    optional = arg_parser.add_argument_group('optional arguments')

    required.add_argument('-inDir', help='Path to directory containing drawio .xml file '
                                         'and directories with winaudit'
                                         ' and scanoval .html files', required=True,
                          action='store')

    # todo add vms data arguments

    optional.add_argument('-outDir', help='Path to output directory for resulting .json file',
                          action='store')
    optional.add_argument('-servers-template', help='Path to servers parsing template (.json)',
                          action='store')
    optional.add_argument('-drawio-template', help='Path to drawio parsing template (.json)',
                          action='store')
    optional.add_argument('-result-template', help='Path to result template (.json)',
                          action='store')

    optional.add_argument('-creds', help='Path to json file with credentials for Yandex Cloud,'
                                         'VMware Cloud Director, YaCloud Virtual machines and Netbox.',
                          action='store')
    optional.add_argument('-yaCloudEnt', help='Enter this key to retrieve Yandex Cloud entities.',
                          action="store_true", dest="yaCloudEnt")
    optional.add_argument('-yaCloudVM', help='Enter this key to retrieve Yandex Cloud Virtual Machines'
                                             ' audit data.',
                          action="store_true", dest="yaCloudVM")

    optional.add_argument('-vmWareEnt', help='Enter this key to retrieve VMWare Cloud Director'
                                             ' entities.',
                          action="store_true", dest="vmWareEnt")

    optional.add_argument('-uploadNB', help='Enter this key to upload resulting segment to NetBox',
                          action="store_true", dest="uploadNB")

    args = arg_parser.parse_args()

    inputDir = pathlib.Path(args.inDir)
    if not inputDir.exists():
        print("Invalid input dir path")
        quit()

    creds = None
    creds_arg = args.creds
    if creds_arg is not None:
        creds_path = pathlib.Path(creds_arg)
        if creds_path.exists():
            creds = read_json(creds_path)
        else:
            print('Invalid credentials file path')

    yaEnt = False
    yaVM = False
    vmWareEnt = False
    uploadNB = False

    if args.yaCloudEnt:
        if creds is None or "yacloud" not in creds.keys():
            print('For parsing Yandex Cloud entities you must provide credentials json file.')
        else:
            yaEnt = True

    if args.yaCloudVM:
        if creds is None or ("virtual_machines" not in creds.keys() or "yacloud" not in creds.keys()):
            print('For parsing Yandex Cloud virtual machines you must provide credentials json file.')
        else:
            yaVM = True

    if args.vmWareEnt:
        if creds is None or "vmware" not in creds.keys():
            print('For parsing VMWare Cloud Director entities you must provide valid credentials json file.')
        else:
            vmWareEnt = True

    if args.uploadNB:
        if creds is None or "netbox" not in creds.keys():
            print('For uploading data to NetBox you must provide valid credentials json file.')
        else:
            uploadNB = True

    if args.outDir is not None:
        outputDir = pathlib.Path(args.outDir)
    else:
        outputDir = inputDir
    if not inputDir.exists():
        print("Invalid output dir path")
        quit()

    if args.servers_template is None:
        servers_template = pathlib.Path('templates/winaudit_parse_template.json')
    else:
        servers_template = pathlib.Path(args.servers_template)
    if not servers_template.exists() or not servers_template.is_file():
        print("Invalid servers template file path")
        quit()

    if args.drawio_template is None:
        drawio_template = pathlib.Path('templates/drawio_parse_template.json')
    else:
        drawio_template = pathlib.Path(args.drawio_template)
    if not drawio_template.exists() or not drawio_template.is_file():
        print("Invalid drawio template file path")
        quit()

    if args.result_template is None:
        result_template = pathlib.Path('templates/segment_template.json')
    else:
        result_template = pathlib.Path(args.result_template)
    if not result_template.exists() or not result_template.is_file():
        print("Invalid result template file path")
        quit()

    main(inputDir, outputDir, servers_template, drawio_template, result_template, credentials=creds,
         parseYandexCloudEnt=yaEnt, parseYandexCloudVMs=yaVM, parseVMWareCloudEnt=vmWareEnt, uploadNB=uploadNB)
