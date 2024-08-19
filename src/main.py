# -*- coding: utf-8 -*-
import argparse
import sys
from parsers.utils.format_output import AutoIndent
from parsers.ParseMethods import *
from parsers.utils.general import *


def main(input_dir: pathlib.Path, output_dir: pathlib.Path,
         servers_template_path: pathlib.Path, drawio_template_path: pathlib.Path,
         result_template_path: pathlib.Path, yacloud_account_file_path: pathlib.Path = None,
         vms_credentials: dict = None, vmware_creds: dict = None) -> None:

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

    print('-' * 40)
    if yacloud_account_file_path is not None:
        yacloud_account = read_json(yacloud_account_file_path)
        if vms_credentials is not None: # vms_credentials are required for yacloud parsing
            yacloud_servers = parse_yandex_cloud_vms(yacloud_account, vms_credentials)
        else:
            yacloud_servers = {'servers': []}
        yacloud_objects = parse_yandex_cloud_entities(yacloud_account)
    else:
        yacloud_servers = {'servers': []}
        yacloud_objects = {}

    print('-' * 40)
    if vmware_creds is not None:
        vmware_objects = parse_vmware_cloud_director_entities(vmware_creds, vmware_creds['vcd'])
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


if __name__ == '__main__':
    sys.stdout = AutoIndent(sys.stdout)
    arg_parser = argparse.ArgumentParser('WinAudit parser')

    required = arg_parser.add_argument_group('required arguments')
    optional = arg_parser.add_argument_group('optional arguments')

    required.add_argument('-inDir', help='Path to directory containing drawio .xml file '
                                         'and directories with winaudit'
                                         ' and scanoval .html files', required=True)

    # todo add vms data arguments

    optional.add_argument('-outDir', help='Path to output directory for resulting .json file')
    optional.add_argument('-servers-template', help='Path to servers parsing template (.json)')
    optional.add_argument('-drawio-template', help='Path to drawio parsing template (.json)')
    optional.add_argument('-result-template', help='Path to result template (.json)')

    optional.add_argument('-yaCloudAcc', help='Path to json file with oauth token organization, cloud and folder data'
                                              'for accessing virtual machines on Yandex.Cloud.')
    optional.add_argument('-vmCredSrc', help='Way to get credentials for accessing virtual machines on '
                                             'Yandex.Cloud. Choose from (json)')
    optional.add_argument('-vmCredJson', help='Path to json containing credentials for'
                                              ' accessing virtual machines on Yandex.Cloud.')

    optional.add_argument('-vmWareCloudAcc', help='Path to json file with host url, username, password'
                                                  'and tenant name for accessing VMWare Cloud Director API.')

    args = arg_parser.parse_args()

    inputDir = pathlib.Path(args.inDir)
    if not inputDir.exists():
        print("Invalid input dir path")
        quit()

    # long validation of virtual machines arguments
    ya_cloud_acc = args.yaCloudAcc
    ya_cloud_acc_path = None
    vmCreds = None
    if ya_cloud_acc is not None:  # if cloud info is provided (i.e. user wants to get data from yacloud)
        ya_cloud_acc_path = pathlib.Path(ya_cloud_acc)
        if ya_cloud_acc_path.exists():  # and cloud data json path is correct
            vmCredSrc = str(args.vmCredSrc)
            if vmCredSrc == 'json':  # looking for a way to get creds
                if args.vmCredJson is not None:  # if choice is json and file path provided
                    credPath = pathlib.Path(args.vmCredJson)
                    if credPath.exists():  # validating path and retrieving json as dict
                        with open(credPath, 'r', encoding='utf-8') as file:
                            vmCreds = json.load(file)
                    else:
                        print('Invalid vmCredJson path')  # if invalid - quit
                        quit()
                else:  # if no json path provided - quit
                    print('If vmCredSrc=json you should provide path to json with key -vmCredJson')
                    quit()
            elif vmCredSrc == 'None':
                pass
            else:
                print('No -vmCredSrc provided to scan virtual machines on Yandex cloud.')
                quit()

    vmware_acc = args.vmWareCloudAcc
    vmware_creds = None
    if vmware_acc is not None:
        vmware_path = pathlib.Path(vmware_acc)
        if vmware_path.exists():
            with open(vmware_path, 'r', encoding='utf-8') as file:
                vmware_creds = json.load(file)
        else:
            print('Invalid vmWareCloudAcc path')

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

    main(inputDir, outputDir, servers_template, drawio_template, result_template, ya_cloud_acc_path, vmCreds,
         vmware_creds)
