# -*- coding: utf-8 -*-
import argparse
from parsers.ParseMethods import *
from parsers.utils.general import *


def main(input_dir: pathlib.Path, output_dir: pathlib.Path,
         servers_template_path: pathlib.Path, drawio_template_path: pathlib.Path,
         result_template_path: pathlib.Path, yacloud_account_file_path: pathlib.Path = None,
         vms_credentials: dict = None) -> None:

    # handle bad json file
    servers_template = read_json(servers_template_path)
    drawio_template = read_json(drawio_template_path)
    result_template = read_json(result_template_path)
    if yacloud_account_file_path is not None:
        yacloud_account = read_json(yacloud_account_file_path)

    drawio_file = [x for x in input_dir.iterdir() if x.name.endswith('.xml') or x.name.endswith('.drawio')]
    if len(drawio_file) == 0:
        print(f"No drawio file founded in '{input_dir}'. Using segment template instead.")
        segment = result_template
    else:
        with open(drawio_file[0], 'r', encoding='utf-8') as file:
            segment = parse_drawio(file, drawio_template, result_template)

    local_servers = parse_local_servers(input_dir, servers_template)

    if yacloud_account_file_path is not None:
        # vms_credentials are required for yacloud parsing
        # yacloud_servers = parse_yandex_cloud_vms(yacloud_account, vms_credentials)
        ya_ent = parse_yandex_cloud_entities(yacloud_account, vms_credentials)
    else:
        # yacloud_servers = {'servers': []}
        ya_ent = {}

    #servers = {'servers': local_servers['servers'] + yacloud_servers['servers']}
    segment['segment'][0]['servers'] = local_servers['servers']
    segment['yacloud'] = ya_ent

    output_file = output_dir.joinpath('result.json')
    with open(output_file.absolute(), 'w', encoding='utf-8') as file:
        json.dump(segment, file, ensure_ascii=False, indent=4)
        print(f'Saved as {output_file}')


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser('WinAudit parser')

    required = arg_parser.add_argument_group('required arguments')
    optional = arg_parser.add_argument_group('optional arguments')

    required.add_argument('-inDir', help='Path to directory containing drawio .xml file '
                                         'and directoires with winaudit'
                                         ' and scanoval .html files', required=True)

    # todo add vms data arguments

    optional.add_argument('-outDir', help='Path to output directory for resulting .json file')
    optional.add_argument('-servers-template', help='Path to servers parsing template (.json)')
    optional.add_argument('-drawio-template', help='Path to drawio parsing template (.json)')
    optional.add_argument('-result-template', help='Path to result template (.json)')

    optional.add_argument('-yaCloudAcc', help='Path to json file with organization, cloud and folder data'
                                              'for accessing virtual machines on Yandex.Cloud.')
    optional.add_argument('-vmCredSrc', help='Way to get credentials for accessing virtual machines on '
                                             'Yandex.Cloud. Choose from (json)')
    optional.add_argument('-vmCredJson', help='Path to json containing credentials for'
                                              ' accessing virtual machines on Yandex.Cloud.')

    args = arg_parser.parse_args()

    inputDir = pathlib.Path(args.inDir)
    if not inputDir.exists():
        print("Ivalid input dir path")
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
            elif vmCredSrc == 'None':  # if cloud data provided but no way provided - quit()
                print('No -vmCredSrc provided to scan virtual machines on Yandex cloud.')
                quit()
            else:
                print('Invalid choice for -vmCredSrc')
                quit()

    if args.outDir is not None:
        outputDir = pathlib.Path(args.outDir)
    else:
        outputDir = inputDir
    if not inputDir.exists():
        print("Ivalid output dir path")
        quit()

    if args.servers_template is None:
        servers_template = pathlib.Path('templates/winaudit_parse_template.json')
    else:
        servers_template = pathlib.Path(args.servers_template)
    if not servers_template.exists() or not servers_template.is_file():
        print("Ivalid servers template file path")
        quit()

    if args.drawio_template is None:
        drawio_template = pathlib.Path('templates/drawio_parse_template.json')
    else:
        drawio_template = pathlib.Path(args.drawio_template)
    if not drawio_template.exists() or not drawio_template.is_file():
        print("Ivalid drawio template file path")
        quit()

    if args.result_template is None:
        result_template = pathlib.Path('templates/segment_template.json')
    else:
        result_template = pathlib.Path(args.result_template)
    if not result_template.exists() or not result_template.is_file():
        print("Ivalid result template file path")
        quit()

    main(inputDir, outputDir, servers_template, drawio_template, result_template, ya_cloud_acc_path, vmCreds)