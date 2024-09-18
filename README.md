# Infrastructure parser

Parser of *WinAudit*, *ScanOVAL* and *DrawIO* files, combining data in single *json* file.

# How To Use

## Quick start
```
python main.py -inDir <Path to input directory>
```
Script will scan `-inDir` directory for `.drawio`(`.xml`) file and nested directories for _scanOVAl_ and _WinAudit_ `.html` files. ```result.json``` will be saved in ```-inDir``` directory.

### Input directory structure example

```
├── inputDir
│   ├── 113
│   │   ├── scanoval.html
│   │   ├── winaudit.html
│   ├── 233
│   │   ├── winaudit.html
│   ├── directory_name
│   │   ├── scanoval.html
│   ├── diagram.drawio
```

> Note that `id` for server with files in directory `inputDir/directory_name` will be generated automatically, but for servers with files in `inputDir/113`  and `inputDir/233` `id`'s will be **113** and **233** respectively.

___
## Keys usage

```
usage:  WinAudit parser [-h] -inDir INDIR [-outDir OUTDIR] [-servers-template SERVERS_TEMPLATE]
        [-drawio-template DRAWIO_TEMPLATE] [-result-template RESULT_TEMPLATE]
        [-creds CREDS] [-yaCloudEnt] [-yaCloudVM] [-vmWareEnt] [-uploadNB]

      options:
        -h, --help            show this help message and exit

      required arguments:
        -inDir INDIR          Path to directory containing drawio .xml file and directories with winaudit and scanoval .html files

      optional arguments:
        -outDir OUTDIR        Path to output directory for resulting .json file
        -servers-template SERVERS_TEMPLATE
                              Path to servers parsing template (.json)
        -drawio-template DRAWIO_TEMPLATE
                              Path to drawio parsing template (.json)
        -result-template RESULT_TEMPLATE
                              Path to result template (.json)
        -creds CREDS          Path to json file with credentials for Yandex Cloud, VMware Cloud Director and YaCloud Virtual machines.
        -yaCloudEnt           Enter this key to retrieve Yandex Cloud entities.
        -yaCloudVM            Enter this key to retrieve Yandex Cloud Virtual Machines audit data.
        -vmWareEnt            Enter this key to retrieve VMWare Cloud Director entities.
        -uploadNB             Enter this key to upload resulting segment to NetBox
```
___

## Templates usage

### Servers template structure example

```json
{
    "templates": [
        {
            "section_name": "blank section name",
            "type": "blank",
            "html_section_name": "",
            "template": {
                "server_key_name": ""
            }
        },
        {
            "section_name": "ip",
            "type": "list",
            "html_section_name": "Network Adapters",
            "template": {
                "address": "IP Address",
                "netmask": "IP Subnet"
            }
        },
        {
            "section_name": "any name",
            "type": "head",
            "html_section_name": "Обзор системы",
            "template": {
                "name": "Computer Name"
            }
        }
    ]
}
```

Script looks for tables in *WinAudit* file named `"html_section_name"` and maps
 rows to template keys.
#### Example:
 
* In *WinAudit* file, **table** named `"Network Adapters"` has **row** `"IP Address"` with **value** `"0.0.0.0"`
* Template file has `"template"` object with `"section_name": "ip"` **key-value pair**
* `"ip"`'s `"template"` object maps `"IP Address"` to `"address"`
* `"server"` object in result file will have `"ip"` object with `"address": "0.0.0.0"` **key-value pair**

#### Types descriptions
* `"type: "head"` template will add values directly to `"server"` object. 
* `"type: "list"` template will add a list named `"section_name"` with `"template"` objects.
* Script adds `"type": "blank"`  template as empty list named `"section_name"`. 

> Script can map many tables to one section in server object. Just add `"template"` object with equal `"section_name"` and different `"html_section_name"` to `"templates"` list.

### Drawio parse template structure example
```json
{
    "figures_recognition": {
        "hardware": {
            "param": "rounded",
            "value": "0"
        },
        "external_media": {
            "param": "shape",
            "value": "cylinder3"
        },
        "shd": {
            "param": "rhombus",
            "value": ""
        }
    },
    "figures_text_mapping": {
        "hardware": {
            "name": "name",
            "tag": "tag",
            "Model": "model",
            "servers": "servers"
        },
        "external_media": {
            "name": "name",
            "tag": "tag",
            "type": "type"
        },
        "shd": {
            "name": "name",
            "tag": "tag",
            "type": "type"
        }
    }
}
```

Script uses `"figures_recognition"` object to map infrastructure objects types to shapes in `.drawio` file.


* If `"value"` is **empty string**, script will map any shape that has `"param"` value in `<style>` attributes.
* If `"value"` has **string value**, script will map shape that has `"param"` with value `"value"` in `<style>` attributes.

> Consider using shapes with non-overlapping  `<style>` attributes to proper mapping.

Script uses `"figures_text_mapping"` object to retrieve data from shapes and map it to segment objects <br>
In  `"figures_text_mapping"` objects:
* **Key** represents key of **segment** object
* **Value** represents key of shape data. **Segment** objects then will have shape's data values.


> **Keys of `"figures_recognition"` and `"figures_text_mapping"` must be equal.**




#### Example:

* Shape "Rectangle" has data:
    ```
    name: super name;
    tag: cool tag;
    model: awesome model;     
    ```
* `"figures_recognition"` has object `"hardware"`:
    ```json
    "hardware": {
            "param": "rounded",
            "value": "0"
        }
    ```
* `"figures_text_mapping"` has object `"hardware"`:
    ```json
     "hardware": {
            "name": "name",
            "tag": "tag",
            "Model": "model",
            "servers": "servers"
        }
    ```
* In resulting file, "`hardware`" list will have object with key-value pairs:
    ```json
    {
        "name": "super name",
        "tag": "cool tag",
        "SN": "string", // Default segment value
        "Model": "awesome model",
        "OS_apply": true, // Default segment value
        ...
    }
    ```

### Drawio file structure
**Data/text in shapes should match following regular expression:** 
```
^([а-яА-ЯёЁ\w\-\_\@\s]+:\s*(([а-яА-ЯёЁ\w\-\_\@\s]+)|(\[([0-9]+,*)+\]))\s*;)+$
```
 
**I.e. text in shapes should look like:**
```
key: value; 
other key: other_value;
```

May contain list of numeric values (e.g., `"id"`'s of servers for `"hardware"` objects) 
```
servers: [1,2,3];
```

### Credentials template

```json
{
    "yacloud":{
        "key_data_path": "<full_path_to_authorized-key_data_json>",
        "org": "org-name",
        "cloud": "cloud-name",
        "folder": "folder-name"
      },
      "vmware": {
        "user": "username",
        "password": "password",
        "org": "org-name",
        "host": "https://<address_of_vmware_cloud>/",
        "vdc": "vdc-name"
      },
      "virtual_machines": [
            {
              "id": "vm-id",
              "user": "ssh-vm-user",
              "pass": "ssh-key-passprashe",
              "keys_paths": "<full_path_to_ssh_private_key>"
            }
        ],
      "netbox":{
        "host": "http://<your_netbox_address>",
        "token": "api_token"
      }
}
```

Parser uses Yandex Cloud Service Account with `Auditor` and `Viewer` roles on both cloud and folder. Script exchanges `jwt-token` for `iam-token`. To create `jwt-token`, you should provide authorized key data:

```json
{
  "private_key":"PLEASE DO NOT REMOVE THIS LINE! e.t.c",
  "key_id": "",
  "service_account_id": ""
}
```

> More on API authorizing:  <br>
> https://yandex.cloud/ru/docs/iam/operations/iam-token/create-for-sa <br>
> https://yandex.cloud/ru/docs/iam/operations/authorized-key/create <br>
> https://yandex.cloud/ru/docs/iam/operations/sa/set-access-bindings


### Segment template structure

<details>
<summary>Long segment json</summary>

```json
{
"segment": [
{
  "name": "test",
  "address": "string",
  <...some values...>
  "servers_apply": true,
  "servers": [
    {
      "id": 123,
      "name": "",
      "tag": "",
      "OS_name": "",
      "ip": [
        {
          "address": "",
          "netmask": "",
          "iface": ""
        }
      ],
      "process": [
        {
          "address": "",
          "port": 123,
          "protocol": "",
          "process": ""
        }
      ],
      "package": [
        {
          "name": "",
          "version": "",
          "type": ""
        }
      ],
      "vulns": [
        {
          "title": "",
          "severity": "",
          "name": "",
          "version": ""
        }
      ]
    }
  ],
  "hardware_apply": true,
  "hardware": [
    {
      "name": "Web-сервер",
      "tag": "",
      "SN": "string",
      "Model": "string",
      "OS_apply": true,
      "OS_name": "string",
      "ip": "",
      "locations": "",
      "rack_locatoins": "",
      "servers": [
        {
          "id": 123
        }
      ],
      "virtualization_apply": true,
      "virtualization_name": "string",
      "virtual_servers": [
        {
          "id": 1
        }
      ]
    }
  ],
  "controllers_apply": false,
  "controllers": [
    {
      "name": "",
      "tag": "",
      "SN": "string",
      "Model": "string",
      "OS_apply": true,
      "OS_name": "string",
      "ip": "",
      "type": "scada",
      "locations": "",
      "rack_locatoins": ""
    }
  ],
  "external_media_apply": false,
  "external_media": [
    {
      "tag": "",
      "name": "",
      "type": "",
      "registration_number": "",
      "SN": ""
    }
  ],
  "shd_apply": false,
  "shd": [
    {
      "tag": "",
      "name": "",
      "model": "",
      "OS_apply": true,
      "OS_name": "string",
      "locations": "",
      "rack_locatoins": "",
      "type": "",
      "services": [
        {
          "apply": true,
          "ML": false
        }
      ],
      "port": [
        {
          "apply": false,
          "number": 80,
          "protocol": "https",
          "service": "nginx"
        }
      ]
    }
  ],
  "telecom_apply": true,
  "telecom": [
    {
      "tag": "",
      "type": "",
      "name": "example",
      "SN": "string",
      "model": "string",
      "OS": "string",
      "ip": "",
      "locations": "",
      "rack_locatoins": ""
    }
  ],
  "virtual_segment_apply": false,
  "virtual_segment": [
    {
      "operator": "example",
      "model": "",
      "name": "example",
      "tag": "",
      "dns": "",
      "attestations_apply": false,
      "locations": "",
      "attestations": [
        {
          "name": "",
          "date": "",
          "number": ""
        }
      ],
      "guard": "string",
      "fire_safety": "string",
      "electricity": "string",
      "KZ": "string",
      "conditions": "string",
      "rent": {
        "contract_number": 0,
        "contract_date": "string",
        "name": "string",
        "owner": "string",
        "matrix_risk": {
          "url": "string",
          "number": "string",
          "date": "string"
        }
      },
      "services": [
        {
          "name": "",
          "tag": "",
          "type": ""
        }
      ],
      "virtual_servers": [
        {
          "id": 0
        }
      ]
    }
  ]
}
]
}
```
</details>

Segment template contains templates for network entities, such as `hardware`, `shd` e.t.c. `"servers"` list will contain local servers and cloud virtual machines. Script also maps processed fields from `.drawio` diagram to segment template objects. 

For example, if diagram `hardware` template contains only `"name": "name"`, in result file other fields will have values from segment template.  

Yandex Cloud and VMWare Cloud Director entities placed in `yacloud` and `vmware_cloud_director` respectively.

